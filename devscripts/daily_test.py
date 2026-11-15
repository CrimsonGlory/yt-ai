#!/usr/bin/env python3
"""Daily full-suite run: make test, log results, Grok-fix failures.

Runs `make test` (pytest -Werror plus ruff/autopep8). Parses the pytest
summary (``19 failed, 5587 passed, …``), then launches one `grok` process
with a self-contained prompt when anything failed. Skips Grok when green.
Grok is told to create **one commit per independent fix** (usually one
extractor). If it still writes a combined commit, this script splits it.

Intended to be run once a day from cron via ./daily_test.sh (flock + logs).

Examples:

    python3 devscripts/daily_test.py --dry-run
    python3 devscripts/daily_test.py --no-grok
    python3 devscripts/daily_test.py --from-log tmp/daily-test/pytest-latest.log
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROMPT_TEMPLATE = Path(__file__).resolve().parent / 'daily_test.prompt.md'
DEFAULT_LOG_DIR = REPO / 'tmp' / 'daily-test'
PROGRESS_NAME = 'progress.jsonl'
DEFAULT_TEST_CMD = ['make', 'test']

ANSI_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
# ========= 19 failed, 5587 passed, 2656 skipped in 10322.93s (2:52:02) ==========
SUMMARY_LINE_RE = re.compile(
    r'^=+\s*(.+?)\s+in\s+([\d.]+)s(?:\s+\(([^)]+)\))?\s*=+\s*$',
)
COUNT_RE = re.compile(
    r'(\d+)\s+(failed|passed|skipped|error|errors|xfailed|xpassed|'
    r'warning|warnings|deselected)',
)
FAILED_LINE_RE = re.compile(
    r'^(FAILED|ERROR)\s+(\S+?)(?:\s+-+\s+.*)?\s*$',
)
SHORT_SUMMARY_RE = re.compile(r'short test summary info', re.I)
FIX_BULLET_RE = re.compile(r'^-\s+([^:]+):\s+(.+)$', re.M)

SHARED_EXTRACTOR_STEMS = {
    '_extractors', 'extractors', 'common', 'commonprotocols', 'lazy_extractors',
}
SHARED_PATHS = {
    'README.md',
    'supportedsites.md',
    'live-site-status.csv',
    'Changelog.md',
    'CONTRIBUTING.md',
    'yt_dlp/extractor/_extractors.py',
}
COMMITTABLE_PREFIXES = (
    'yt_dlp/',
    'test/',
    'devscripts/',
)
COMMITTABLE_FILES = SHARED_PATHS | {
    'pyproject.toml',
    'Makefile',
    'AGENTS.md',
}
SKIP_SUFFIXES = {
    '.pyc', '.pyo', '.mp4', '.m4a', '.webm', '.mkv', '.m3u8', '.ts',
    '.dump', '.part', '.ytdl', '.log',
}


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description='Run make test, log results, and Grok-fix failures (one commit per fix).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument('--log-dir', type=Path, default=DEFAULT_LOG_DIR,
                   help='Where to write pytest logs, prompt, grok log, progress')
    p.add_argument('--test-cmd', default='make test',
                   help='Shell-ish command for the full suite (default: make test)')
    p.add_argument('--from-log', type=Path,
                   help='Skip the suite; parse this existing make/pytest log')
    p.add_argument('--from-junit', type=Path,
                   help='JUnit XML to parse (default: alongside --from-log or this run)')
    p.add_argument('--dry-run', action='store_true',
                   help='Run/parse tests and write the prompt; do not invoke Grok')
    p.add_argument('--no-grok', action='store_true',
                   help='Never invoke Grok, even if tests failed')
    p.add_argument('--no-commit', action='store_true',
                   help='Do not commit (default: one commit per independent fix)')
    p.add_argument('--test-timeout', type=int, default=0,
                   help='Seconds for make test (0 = no limit)')
    p.add_argument('--timeout', type=int, default=14400,
                   help='Seconds for the Grok invocation (0 = no limit; default 4h)')
    p.add_argument('--max-turns', type=int, default=200, help='Grok --max-turns')
    p.add_argument('--max-failures', type=int, default=40,
                   help='Max failing nodeids to embed in the Grok prompt')
    p.add_argument('--grok-bin', default=os.environ.get('GROK_BIN', 'grok'),
                   help='Grok executable')
    p.add_argument('--model', default=os.environ.get('GROK_MODEL', ''),
                   help='Optional grok --model')
    p.add_argument('--grok-arg', action='append', default=[],
                   help='Extra arg passed through to grok (repeatable)')
    return p.parse_args(argv)


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub('', text.replace('\r', ''))


def git(args: list[str], check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ['git', *args],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        check=check,
    )


def git_out(args: list[str]) -> str:
    proc = git(args)
    if proc.returncode != 0:
        raise RuntimeError(
            f'git {" ".join(args)} failed ({proc.returncode}): '
            f'{(proc.stderr or proc.stdout).strip()}')
    return (proc.stdout or '').strip()


def merge_in_progress() -> bool:
    return (REPO / '.git' / 'MERGE_HEAD').exists()


def _norm_path(path: str) -> str:
    return path.replace('\\', '/').lstrip('./')


def is_committable_path(path: str) -> bool:
    """Source / docs we may commit; never media dumps, logs, or tmp."""
    norm = _norm_path(path)
    if not norm or norm.startswith('tmp/') or '/__pycache__/' in f'/{norm}/':
        return False
    suffix = Path(norm).suffix.lower()
    if suffix in SKIP_SUFFIXES:
        return False
    if norm in COMMITTABLE_FILES:
        return True
    return any(norm.startswith(prefix) for prefix in COMMITTABLE_PREFIXES)


def site_extractor_group(path: str) -> str | None:
    """Return ``ie:<name>`` for a per-site extractor module, else None."""
    norm = _norm_path(path)
    prefix = 'yt_dlp/extractor/'
    if not norm.startswith(prefix) or not norm.endswith('.py'):
        return None
    rest = norm[len(prefix):]
    top = rest.split('/', 1)[0]
    if top.endswith('.py'):
        stem = top[:-3]
        if stem in SHARED_EXTRACTOR_STEMS:
            return None
        return f'ie:{stem}'
    if top in SHARED_EXTRACTOR_STEMS:
        return None
    return f'ie:{top}'


def group_key_for_path(path: str) -> str:
    """Group files so each independent fix becomes its own commit."""
    norm = _norm_path(path)
    ie = site_extractor_group(norm)
    if ie:
        return ie
    if norm.startswith('test/') and norm.endswith('.py'):
        return f'test:{Path(norm).name}'
    if norm in SHARED_PATHS:
        return 'shared'
    return 'core'


def primary_groups(paths: list[str]) -> set[str]:
    return {
        group_key_for_path(p)
        for p in paths
        if is_committable_path(p) and group_key_for_path(p) != 'shared'
    }


def parse_fix_bullets(message: str) -> dict[str, str]:
    """Parse ``- ExtractorName: what changed`` lines from a commit body."""
    out: dict[str, str] = {}
    for m in FIX_BULLET_RE.finditer(message or ''):
        name = m.group(1).strip()
        text = m.group(2).strip()
        if name and text:
            out[name] = text
    return out


def match_bullet(stem: str, bullets: dict[str, str]) -> tuple[str | None, str]:
    stem_raw = stem.lower()
    stem_cmp = stem_raw.replace('_', '')
    for name, text in bullets.items():
        n = name.lower()
        if n == stem_raw or n.replace('_', '') == stem_cmp:
            return name, text
    return None, ''


def commits_since(old_head: str) -> list[str]:
    if not old_head:
        return []
    proc = git(['log', '--format=%H %s', f'{old_head}..HEAD'])
    if proc.returncode != 0:
        return []
    return [ln.strip() for ln in (proc.stdout or '').splitlines() if ln.strip()]


def _paths_from_git(args: list[str]) -> list[str]:
    proc = git(args)
    if proc.returncode != 0:
        return []
    return [ln.strip() for ln in (proc.stdout or '').splitlines() if ln.strip()]


def changed_source_paths_since(old_head: str) -> list[str]:
    paths: set[str] = set()
    for args in (
        ['diff', '--name-only', old_head],
        ['diff', '--name-only', '--cached', old_head],
        ['ls-files', '--others', '--exclude-standard'],
    ):
        paths.update(_paths_from_git(args))
    return sorted(p for p in paths if is_committable_path(p))


def uncommitted_source_paths() -> list[str]:
    paths: set[str] = set()
    for args in (
        ['diff', '--name-only'],
        ['diff', '--name-only', '--cached'],
        ['ls-files', '--others', '--exclude-standard'],
    ):
        paths.update(_paths_from_git(args))
    return sorted(p for p in paths if is_committable_path(p))


def commit_file_list(sha: str) -> list[str]:
    proc = git(['diff-tree', '--no-commit-id', '--name-only', '-r', sha])
    if proc.returncode != 0:
        return []
    return [ln.strip() for ln in (proc.stdout or '').splitlines() if ln.strip()]


def commits_are_already_split(old_head: str) -> bool:
    """True when each new commit has at most one primary fix group."""
    proc = git(['log', '--format=%H', f'{old_head}..HEAD'])
    if proc.returncode != 0:
        return False
    shas = [ln.strip() for ln in (proc.stdout or '').splitlines() if ln.strip()]
    if not shas:
        return False
    return all(len(primary_groups(commit_file_list(sha))) <= 1 for sha in shas)


def bullets_from_existing(commit_lines: list[str]) -> dict[str, str]:
    """Recover extractor names/bodies from Grok's combined or split commits."""
    bullets: dict[str, str] = {}
    for line in commit_lines:
        sha, _, subject = line.partition(' ')
        with contextlib.suppress(RuntimeError):
            bullets.update(parse_fix_bullets(
                git_out(['log', '-1', '--format=%B', sha])))
        m = re.match(r'\[daily-test\] Fix (.+)$', subject.strip())
        if not m:
            continue
        name = m.group(1).strip()
        if name and not any(k.lower() == name.lower() for k in bullets):
            bullets[name] = ''
    return bullets


def stage_paths(paths: list[str]) -> bool:
    added = False
    for path in paths:
        full = REPO / path
        if full.exists():
            proc = git(['add', '--', path])
        else:
            proc = git(['add', '-u', '--', path])
        if proc.returncode != 0:
            eprint(f'warning: git add {path} failed: {(proc.stderr or "").strip()}')
            continue
        added = True
    return added


def message_for_group(key: str, bullets: dict[str, str]) -> tuple[str, str]:
    if key.startswith('ie:'):
        stem = key.split(':', 1)[1]
        name, body = match_bullet(stem, bullets)
        display = name or stem
        return (
            f'[daily-test] Fix {display}',
            body or f'Fix the failing {display} test.',
        )
    if key.startswith('test:'):
        name = key.split(':', 1)[1]
        return f'[daily-test] Fix {name}', f'Fix failing tests in {name}.'
    if key == 'core':
        return '[daily-test] Fix core', 'Fix failing core / shared-library tests.'
    return (
        '[daily-test] Update changelog and site metadata',
        (
            'Record fork-changelog, supported-sites, or live-site-status '
            'updates for the daily-test fixes.'
        ),
    )


def commit_path_groups(paths: list[str], bullets: dict[str, str]) -> list[str]:
    groups: dict[str, list[str]] = {}
    for path in paths:
        if not is_committable_path(path):
            continue
        groups.setdefault(group_key_for_path(path), []).append(path)

    shared = groups.pop('shared', [])
    primary_keys = list(groups)
    if shared and len(primary_keys) == 1:
        groups[primary_keys[0]].extend(shared)
        shared = []
    elif shared:
        groups['shared'] = shared

    def sort_key(k: str) -> tuple[int, str]:
        if k.startswith('ie:'):
            return (0, k)
        if k.startswith('test:'):
            return (1, k)
        if k == 'core':
            return (2, k)
        return (3, k)

    created: list[str] = []
    for key in sorted(groups, key=sort_key):
        files = sorted(set(groups[key]))
        if not stage_paths(files):
            continue
        staged = (git(['diff', '--cached', '--name-only']).stdout or '').strip()
        if not staged:
            continue
        subject, body = message_for_group(key, bullets)
        msg = f'{subject}\n\n{body}' if body else subject
        proc = git(['commit', '-m', msg])
        if proc.returncode != 0:
            eprint(
                f'warning: git commit failed for {key}: '
                f'{(proc.stderr or proc.stdout or "").strip()}')
            git(['reset', '-q', 'HEAD'])
            continue
        try:
            full = git_out(['rev-parse', 'HEAD'])
            short = git_out(['rev-parse', '--short', 'HEAD'])
        except RuntimeError as exc:
            eprint(f'warning: {exc}')
            continue
        created.append(f'{full} {subject}')
        eprint(f'+ commit {short} {subject}')
    return created


def finalize_per_fix_commits(old_head: str) -> list[str]:
    """Ensure Grok's work is one commit per independent fix.

    If Grok already committed that way, leave those commits. If it wrote
    one combined commit (or left a dirty tree), split by extractor /
    test module.
    """
    if merge_in_progress():
        eprint('warning: merge in progress; not splitting commits')
        return commits_since(old_head)

    existing = commits_since(old_head)
    leftover = uncommitted_source_paths()
    bullets = bullets_from_existing(existing)

    if commits_are_already_split(old_head) and not leftover:
        eprint(f'Grok already created {len(existing)} per-fix commit(s)')
        return existing

    if commits_are_already_split(old_head) and leftover:
        eprint(
            f'Grok created {len(existing)} per-fix commit(s); '
            'committing leftovers separately')
        return existing + commit_path_groups(leftover, bullets)

    try:
        head_now = git_out(['rev-parse', 'HEAD'])
    except RuntimeError as exc:
        eprint(f'warning: {exc}')
        return existing

    if head_now != old_head:
        eprint('Splitting combined daily-test commit(s) into per-fix commits')
        proc = git(['reset', '--soft', old_head])
        if proc.returncode != 0:
            eprint(
                f'warning: git reset --soft failed: '
                f'{(proc.stderr or "").strip()}')
            return existing
        proc = git(['reset', '-q', 'HEAD'])
        if proc.returncode != 0:
            eprint(
                f'warning: git reset (unstage) failed: '
                f'{(proc.stderr or "").strip()}')
            return commits_since(old_head)

    paths = changed_source_paths_since(old_head)
    if not paths:
        return commits_since(old_head)
    return commit_path_groups(paths, bullets)


def last_lines(text: str, n: int = 12) -> str:
    lines = [ln.rstrip() for ln in strip_ansi(text).splitlines()]
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines[-n:])


def _norm_count_key(kind: str) -> str:
    if kind in ('error', 'errors'):
        return 'errors'
    if kind in ('warning', 'warnings'):
        return 'warnings'
    return kind


def parse_summary_line(line: str) -> dict | None:
    m = SUMMARY_LINE_RE.match(line.strip())
    if not m:
        return None
    body, seconds, human = m.group(1), m.group(2), m.group(3)
    counts = {
        'failed': 0, 'passed': 0, 'skipped': 0, 'errors': 0,
        'xfailed': 0, 'xpassed': 0, 'warnings': 0, 'deselected': 0,
    }
    found = False
    for n, kind in COUNT_RE.findall(body):
        counts[_norm_count_key(kind)] = int(n)
        found = True
    if not found:
        return None
    return {
        'line': line.strip(),
        'seconds': seconds,
        'human_duration': human or '',
        **counts,
    }


def parse_pytest_log(text: str) -> dict:
    """Parse pytest / make test stdout for the summary and FAILED nodeids."""
    lines = [strip_ansi(ln).rstrip() for ln in text.splitlines()]
    summary = None
    for ln in reversed(lines):
        s = ln.strip()
        if not s or s.startswith('make:'):
            continue
        summary = parse_summary_line(s)
        if summary:
            break

    failed_tests: list[str] = []
    short_start = None
    for i, ln in enumerate(lines):
        if SHORT_SUMMARY_RE.search(ln):
            short_start = i
    scan = lines[short_start + 1:] if short_start is not None else lines
    for ln in scan:
        if SUMMARY_LINE_RE.match(ln.strip()):
            break
        m = FAILED_LINE_RE.match(ln.strip())
        if m:
            nodeid = m.group(2)
            if nodeid not in failed_tests:
                failed_tests.append(nodeid)

    return {
        'summary': summary,
        'failed_tests': failed_tests,
        'tail': last_lines(text, 16),
    }


def _local_tag(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def _junit_nodeid(case: ET.Element) -> str:
    name = case.attrib.get('name') or 'unknown'
    file = case.attrib.get('file') or ''
    classname = case.attrib.get('classname') or ''
    if file:
        last = classname.rsplit('.', 1)[-1] if classname else ''
        if last and last[:1].isupper():
            return f'{file}::{last}::{name}'
        return f'{file}::{name}'
    if classname:
        return f'{classname}::{name}'
    return name


def parse_junit(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        eprint(f'warning: could not parse junit xml {path}: {exc}')
        return None

    suites = []
    tag = _local_tag(root.tag)
    if tag == 'testsuite':
        suites = [root]
    elif tag == 'testsuites':
        suites = [el for el in root if _local_tag(el.tag) == 'testsuite']
    else:
        suites = [root]

    failed: list[dict] = []
    counts = {'failed': 0, 'errors': 0, 'passed': 0, 'skipped': 0, 'tests': 0}
    time_s = 0.0
    for suite in suites:
        counts['failed'] += int(suite.attrib.get('failures') or 0)
        counts['errors'] += int(suite.attrib.get('errors') or 0)
        counts['skipped'] += int(suite.attrib.get('skipped') or 0)
        counts['tests'] += int(suite.attrib.get('tests') or 0)
        with contextlib.suppress(ValueError):
            time_s += float(suite.attrib.get('time') or 0)
        for case in suite.iter():
            if _local_tag(case.tag) != 'testcase':
                continue
            kind = None
            message = ''
            body = ''
            for child in list(case):
                ctag = _local_tag(child.tag)
                if ctag in ('failure', 'error'):
                    kind = 'failed' if ctag == 'failure' else 'error'
                    message = child.attrib.get('message') or ''
                    body = (child.text or '').strip()
                    break
                if ctag == 'skipped':
                    kind = 'skipped'
                    break
            if kind in ('failed', 'error'):
                failed.append({
                    'nodeid': _junit_nodeid(case),
                    'kind': kind,
                    'message': message,
                    'body': body,
                })
    counts['passed'] = max(
        0, counts['tests'] - counts['failed'] - counts['errors'] - counts['skipped'])
    return {'counts': counts, 'time': time_s, 'failures': failed}


def format_failed_tests(nodeids: list[str], limit: int) -> str:
    if not nodeids:
        return '(no FAILED/ERROR nodeids parsed — read the log tail and junit xml)'
    shown = nodeids[:limit]
    lines = [f'{i}. `{n}`' for i, n in enumerate(shown, 1)]
    hidden = len(nodeids) - len(shown)
    if hidden > 0:
        lines.append(f'… and {hidden} more (see the pytest log / junit xml)')
    return '\n'.join(lines)


def format_excerpts(junit: dict | None, log_text: str, nodeids: list[str],
                    limit: int, per_item: int = 2500) -> str:
    chunks: list[str] = []
    used = set()
    if junit:
        for item in junit.get('failures') or []:
            nodeid = item.get('nodeid') or ''
            if len(chunks) >= limit:
                break
            used.add(nodeid)
            body = item.get('body') or item.get('message') or ''
            if len(body) > per_item:
                body = body[:per_item] + '\n… (truncated)'
            chunks.append(f'### `{nodeid}`\n```\n{body or "(no traceback)"}\n```')
    # Fall back to FAILED lines from the short summary for anything missing.
    remaining = [n for n in nodeids if n not in used]
    if remaining and len(chunks) < limit:
        summary_lines = []
        for ln in strip_ansi(log_text).splitlines():
            m = FAILED_LINE_RE.match(ln.strip())
            if m and m.group(2) in remaining:
                summary_lines.append(ln.strip())
        if summary_lines:
            text = '\n'.join(summary_lines[:limit - len(chunks)])
            chunks.append('### short test summary\n```\n' + text + '\n```')
    if not chunks:
        return '(no excerpts; open the pytest log)'
    return '\n\n'.join(chunks)


def build_prompt(
    template: str,
    *,
    today: str,
    branch: str,
    head: str,
    test_cmd: str,
    test_exit: int,
    summary_line: str,
    failed: int,
    errors: int,
    passed: int,
    skipped: int,
    duration: str,
    failed_tests: str,
    excerpts: str,
    log_tail: str,
    pytest_log: str,
    junit_xml: str,
    do_commit: bool,
) -> str:
    if do_commit:
        commit_instruction = (
            '- Commit **immediately after each independent fix**, before '
            'starting the next failing test. Do not wait until the end. '
            'Do not squash. Do not make one combined commit.\n'
            '- One commit per independent fix. That usually means **one '
            'commit per extractor**. Two failing nodeids for the same '
            'extractor share one commit. Unrelated extractors never share a '
            'commit. A shared core/utils fix that unblocks several tests is '
            'one commit; leftover extractor-specific edits still get their '
            'own commits.\n'
            '- After you have actually re-run the nodeids you claim to have '
            'fixed, git-add **only** the files for this fix (the extractor or '
            'unit-test module, `README.md` if you added/revised this '
            "extractor's fork-changelog bullet, `supportedsites.md` if you "
            "regenerated it for this extractor, `live-site-status.csv` if you "
            "edited this domain's row) and commit:\n"
            '  Subject: `[daily-test] Fix <ExtractorName>`\n'
            '    (unit test: `[daily-test] Fix <test module>`; '
            'ruff/autopep8: `[daily-test] Fix lint`)\n'
            '  Body: 1-3 complete sentences: what failed and what you changed.\n'
            '- Example: GoogleDrive and Instagram both fail → two commits, '
            '`[daily-test] Fix GoogleDrive` and `[daily-test] Fix Instagram`. '
            'Never `[daily-test] Fix 2 failing tests`.\n'
            '- Include `hatch fmt` / ruff fixes for files you touched in that '
            'same commit. A separate lint commit only if the suite failure '
            '*is* codetest.\n'
            '- Do not `git add -A`. Do not amend. Do not push. If you later '
            'touch a file from an earlier commit, make a new commit.\n'
            '- If you fixed nothing, do not commit. Do not create a leftover '
            'catch-all commit at the end.'
        )
    else:
        commit_instruction = (
            '- Do **not** git commit, amend, or push. Leave the working tree '
            'dirty for review. (Operator passed --no-commit.)'
        )
    replacements = {
        '__TODAY__': today,
        '__BRANCH__': branch,
        '__HEAD__': head,
        '__TEST_CMD__': test_cmd,
        '__TEST_EXIT__': str(test_exit),
        '__SUMMARY_LINE__': summary_line or '(no pytest summary line found)',
        '__FAILED_COUNT__': str(failed),
        '__ERROR_COUNT__': str(errors),
        '__PASSED_COUNT__': str(passed),
        '__SKIPPED_COUNT__': str(skipped),
        '__DURATION__': duration or 'unknown',
        '__FAILED_TESTS__': failed_tests,
        '__FAILURE_EXCERPTS__': excerpts,
        '__LOG_TAIL__': log_tail or '(empty)',
        '__PYTEST_LOG__': pytest_log,
        '__JUNIT_XML__': junit_xml or '(none)',
        '__COMMIT_INSTRUCTION__': commit_instruction,
    }
    out = template
    for key, value in replacements.items():
        out = out.replace(key, value)
    return out


def grok_cmd(args, prompt_file: Path) -> list[str]:
    cmd = [
        args.grok_bin,
        '--prompt-file', str(prompt_file),
        '--verbatim',
        '--always-approve',
        '--permission-mode', 'bypassPermissions',
        '--cwd', str(REPO),
        '--no-memory',
        '--no-plan',
        '--no-alt-screen',
        '--output-format', 'plain',
        '--max-turns', str(args.max_turns),
    ]
    if args.model:
        cmd.extend(['--model', args.model])
    cmd.extend(args.grok_arg)
    return cmd


def _killpg(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGTERM)


def run_logged(cmd: list[str], log_file: Path, timeout: int,
               env: dict | None = None) -> int:
    """Run cmd, tee stdout+stderr to log_file and this process's stdout."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    eprint('+', ' '.join(cmd))
    with log_file.open('w', encoding='utf-8') as log:
        log.write('# cmd: ' + ' '.join(cmd) + '\n\n')
        log.flush()
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(REPO),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                start_new_session=True,
                env=env,
            )
        except FileNotFoundError:
            eprint(f'error: {cmd[0]!r} not found on PATH.')
            return 127

        old_int = signal.signal(signal.SIGINT, lambda *_: _killpg(proc))
        try:
            deadline = time.monotonic() + timeout if timeout else None
            assert proc.stdout is not None
            while True:
                if deadline is not None and time.monotonic() > deadline:
                    eprint(f'error: timed out after {timeout}s: {cmd[0]}')
                    _killpg(proc)
                    try:
                        proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                    return 124
                line = proc.stdout.readline()
                if line == '' and proc.poll() is not None:
                    break
                if line:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    log.write(line)
            return proc.wait()
        finally:
            signal.signal(signal.SIGINT, old_int)


def parse_status_from_log(log_file: Path) -> str | None:
    if not log_file.is_file():
        return None
    text = log_file.read_text(encoding='utf-8', errors='replace')
    for token in (
        'STATUS: FIXED',
        'STATUS: PARTIAL',
        'STATUS: BLOCKED',
        'STATUS: FAILED',
        'STATUS: PASSED',
    ):
        if token in text:
            return token.split()[-1]
    return None


def append_progress(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def split_test_cmd(cmd: str) -> list[str]:
    return shlex.split(cmd)


def pytest_env(junit_path: Path) -> dict:
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    # Prefer the interpreter running this script (venv) for `make test`.
    py_bin = str(Path(sys.executable).resolve())
    env['PYTHON'] = py_bin
    py_dir = str(Path(sys.executable).resolve().parent)
    env['PATH'] = py_dir + os.pathsep + env.get('PATH', '')
    extra = f'--junitxml={junit_path}'
    existing = env.get('PYTEST_ADDOPTS', '').strip()
    env['PYTEST_ADDOPTS'] = f'{existing} {extra}'.strip() if existing else extra
    return env


def combine_results(parsed: dict, junit: dict | None) -> dict:
    summary = parsed.get('summary') or {}
    failed_tests = list(parsed.get('failed_tests') or [])
    failed = int(summary.get('failed') or 0)
    errors = int(summary.get('errors') or 0)
    passed = int(summary.get('passed') or 0)
    skipped = int(summary.get('skipped') or 0)
    duration = ''
    if summary.get('human_duration'):
        duration = f"{summary.get('seconds')}s ({summary['human_duration']})"
    elif summary.get('seconds'):
        duration = f"{summary['seconds']}s"
    summary_line = summary.get('line') or ''

    if junit:
        jc = junit['counts']
        if not summary:
            failed = jc['failed']
            errors = jc['errors']
            passed = jc['passed']
            skipped = jc['skipped']
            if junit.get('time'):
                duration = f"{junit['time']:.2f}s"
        for item in junit.get('failures') or []:
            nodeid = item.get('nodeid')
            if nodeid and nodeid not in failed_tests:
                failed_tests.append(nodeid)

    return {
        'summary_line': summary_line,
        'failed': failed,
        'errors': errors,
        'passed': passed,
        'skipped': skipped,
        'duration': duration,
        'failed_tests': failed_tests,
        'tail': parsed.get('tail') or '',
    }


def needs_grok(test_exit: int, result: dict) -> bool:
    if test_exit != 0:
        return True
    return (result['failed'] + result['errors']) > 0


def report_result(test_exit: int, result: dict) -> None:
    eprint('')
    eprint('=== test result ===')
    if result['summary_line']:
        eprint(result['summary_line'])
    else:
        eprint('(no pytest summary line found)')
    eprint(
        f"exit={test_exit}  failed={result['failed']}  errors={result['errors']}  "
        f"passed={result['passed']}  skipped={result['skipped']}  "
        f"duration={result['duration'] or '?'}",
    )
    if result['failed_tests']:
        eprint(f"failed tests ({len(result['failed_tests'])}):")
        for nodeid in result['failed_tests'][:30]:
            eprint(f'  {nodeid}')
        extra = len(result['failed_tests']) - 30
        if extra > 0:
            eprint(f'  … and {extra} more')
    elif test_exit != 0:
        eprint('no FAILED nodeids parsed; last lines:')
        eprint(result['tail'] or '(empty)')
    eprint('===================')


def main(argv=None) -> int:
    args = parse_args(argv)
    if not PROMPT_TEMPLATE.is_file():
        eprint(f'error: prompt template not found: {PROMPT_TEMPLATE}')
        return 2
    if not (REPO / '.git').exists():
        eprint(f'error: not a git checkout: {REPO}')
        return 2

    args.log_dir.mkdir(parents=True, exist_ok=True)
    (args.log_dir / 'grok').mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    stamp = time.strftime('%Y-%m-%dT%H%M%S')

    try:
        branch = git_out(['rev-parse', '--abbrev-ref', 'HEAD'])
        head = git_out(['rev-parse', 'HEAD'])
    except RuntimeError as exc:
        eprint(f'error: {exc}')
        return 2

    if merge_in_progress():
        eprint('warning: MERGE_HEAD exists; a merge is in progress')

    pytest_log = args.from_log
    junit_path = args.from_junit
    test_exit = 0
    test_elapsed = 0.0

    if pytest_log is not None:
        pytest_log = pytest_log.resolve()
        if not pytest_log.is_file():
            eprint(f'error: --from-log not found: {pytest_log}')
            return 2
        eprint(f'Reusing log: {pytest_log}')
        # Infer exit from the log if make reported an error.
        log_text = pytest_log.read_text(encoding='utf-8', errors='replace')
        if re.search(r'^make: \*\*\*', strip_ansi(log_text), re.M):
            test_exit = 1
        if junit_path is None:
            candidate = pytest_log.with_suffix('.xml')
            if candidate.is_file():
                junit_path = candidate
    else:
        pytest_log = args.log_dir / f'pytest-{stamp}.log'
        junit_path = junit_path or (args.log_dir / f'pytest-{stamp}.xml')
        cmd = split_test_cmd(args.test_cmd)
        # `make test` honors PYTHON= from the environment / command line.
        if cmd[:1] == ['make'] and 'PYTHON' not in cmd:
            cmd = [*cmd, f'PYTHON={sys.executable}']
        env = pytest_env(junit_path)
        t0 = time.time()
        test_exit = run_logged(cmd, pytest_log, args.test_timeout, env=env)
        test_elapsed = round(time.time() - t0, 1)
        latest = args.log_dir / 'pytest-latest.log'
        try:
            if latest.exists() or latest.is_symlink():
                latest.unlink()
            latest.symlink_to(pytest_log.name)
        except OSError:
            shutil.copyfile(pytest_log, latest)
        log_text = pytest_log.read_text(encoding='utf-8', errors='replace')

    parsed = parse_pytest_log(log_text)
    junit = parse_junit(junit_path) if junit_path else None
    result = combine_results(parsed, junit)
    if args.from_log and result['failed'] + result['errors'] > 0:
        test_exit = test_exit or 1

    report_result(test_exit, result)

    summary_rec = {
        'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'stamp': stamp,
        'branch': branch,
        'head': head,
        'test_cmd': args.test_cmd,
        'test_exit': test_exit,
        'test_elapsed_s': test_elapsed,
        'summary_line': result['summary_line'],
        'failed': result['failed'],
        'errors': result['errors'],
        'passed': result['passed'],
        'skipped': result['skipped'],
        'duration': result['duration'],
        'failed_tests': result['failed_tests'],
        'pytest_log': str(pytest_log),
        'junit_xml': str(junit_path) if junit_path else None,
    }
    summary_path = args.log_dir / f'summary-{stamp}.json'
    summary_path.write_text(
        json.dumps(summary_rec, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8')
    eprint(f'Summary: {summary_path}')
    eprint(f'Log:     {pytest_log}')

    grok_wanted = needs_grok(test_exit, result)
    progress_path = args.log_dir / PROGRESS_NAME

    if not grok_wanted:
        eprint('Suite passed. Skipping Grok.')
        append_progress(progress_path, {
            **{k: summary_rec[k] for k in (
                'ts', 'stamp', 'head', 'test_exit', 'failed', 'errors',
                'passed', 'skipped', 'pytest_log')},
            'status': 'PASSED',
            'exit_code': 0,
        })
        return 0

    if args.no_grok:
        eprint('--no-grok: not invoking Grok')
        append_progress(progress_path, {
            'status': 'FAILED',
            'exit_code': test_exit or 1,
            'ts': summary_rec['ts'],
            'failed': result['failed'],
            'errors': result['errors'],
            'pytest_log': str(pytest_log),
            'skipped_grok': True,
        })
        return test_exit or 1

    if merge_in_progress():
        eprint('error: merge in progress; refusing to launch Grok (STATUS: BLOCKED)')
        append_progress(progress_path, {
            'status': 'BLOCKED',
            'exit_code': 3,
            'ts': summary_rec['ts'],
            'reason': 'MERGE_HEAD',
            'pytest_log': str(pytest_log),
        })
        return 3

    template = PROMPT_TEMPLATE.read_text(encoding='utf-8')
    duration = result['duration'] or (
        f'{test_elapsed}s' if test_elapsed else 'unknown')
    prompt = build_prompt(
        template,
        today=today,
        branch=branch,
        head=head,
        test_cmd=args.test_cmd,
        test_exit=test_exit,
        summary_line=result['summary_line'],
        failed=result['failed'],
        errors=result['errors'],
        passed=result['passed'],
        skipped=result['skipped'],
        duration=duration,
        failed_tests=format_failed_tests(
            result['failed_tests'], args.max_failures),
        excerpts=format_excerpts(
            junit, log_text, result['failed_tests'], args.max_failures),
        log_tail=result['tail'],
        pytest_log=str(pytest_log),
        junit_xml=str(junit_path) if junit_path and Path(junit_path).is_file() else '',
        do_commit=not args.no_commit,
    )
    prompt_file = args.log_dir / f'prompt-{stamp}.txt'
    prompt_file.write_text(prompt, encoding='utf-8')
    eprint(f'Wrote prompt: {prompt_file}')
    eprint(
        f"Grok will see {min(len(result['failed_tests']), args.max_failures)} "
        f"of {len(result['failed_tests'])} failing nodeids "
        f"(failed={result['failed']} errors={result['errors']})",
    )

    if args.dry_run:
        eprint('dry-run: would exec:', ' '.join(grok_cmd(args, prompt_file)[:8]), '…')
        append_progress(progress_path, {
            'status': 'DRY_RUN',
            'exit_code': 0,
            'ts': summary_rec['ts'],
            'failed': result['failed'],
            'errors': result['errors'],
            'prompt': str(prompt_file),
            'pytest_log': str(pytest_log),
        })
        return 0

    grok_log = args.log_dir / 'grok' / f'{stamp}.log'
    t0 = time.time()
    rc = run_logged(grok_cmd(args, prompt_file), grok_log, args.timeout)
    elapsed = round(time.time() - t0, 1)
    status = parse_status_from_log(grok_log)
    if rc == 130:
        status = status or 'ERROR'
    elif rc != 0 and not status:
        status = 'ERROR'
    elif not status:
        status = 'FAILED'

    rec = {
        'status': status,
        'exit_code': rc,
        'elapsed_s': elapsed,
        'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'head_before': head,
        'failed': result['failed'],
        'errors': result['errors'],
        'failed_tests': result['failed_tests'],
        'log': str(grok_log),
        'prompt': str(prompt_file),
        'pytest_log': str(pytest_log),
    }
    if args.no_commit:
        rec['commits'] = commits_since(head)
    else:
        rec['commits'] = finalize_per_fix_commits(head)
    try:
        rec['head_after'] = git_out(['rev-parse', 'HEAD'])
    except RuntimeError:
        rec['head_after'] = None
    append_progress(progress_path, rec)
    eprint(f'-- grok status={status} exit={rc} elapsed={elapsed}s')
    eprint(f'Grok log: {grok_log}')
    if rec.get('commits'):
        eprint(f"Commits ({len(rec['commits'])}):")
        for line in rec['commits']:
            eprint(f'  {line}')
    else:
        eprint('Commits: none')

    if rc == 130:
        return 130
    if status == 'FIXED' and rc == 0:
        return 0
    if status == 'PARTIAL' and rc == 0:
        return 0
    if status == 'BLOCKED':
        return 3
    return 1 if rc == 0 else rc


if __name__ == '__main__':
    raise SystemExit(main())
