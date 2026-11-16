#!/usr/bin/env python3
"""Pull yt-dlp upstream into yt-ai with a Grok session.

Fetches https://github.com/yt-dlp/yt-dlp, skips the LLM when already up to
date, otherwise launches one `grok` process with a self-contained prompt that
merges, compares overlapping site fixes, and always commits.

Intended to be run once a day from cron via ./pull_upstream.sh.

Examples:

    python3 devscripts/pull_upstream.py --dry-run
    python3 devscripts/pull_upstream.py
    python3 devscripts/pull_upstream.py --force
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROMPT_TEMPLATE = Path(__file__).resolve().parent / 'pull_upstream.prompt.md'
DEFAULT_LOG_DIR = REPO / 'tmp' / 'pull-upstream'
DEFAULT_UPSTREAM_URL = 'https://github.com/yt-dlp/yt-dlp.git'
DEFAULT_UPSTREAM_REMOTE = 'upstream'
DEFAULT_UPSTREAM_REF = 'master'
PROGRESS_NAME = 'progress.jsonl'


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description='Fetch yt-dlp and merge it into yt-ai with a Grok session.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument('--log-dir', type=Path, default=DEFAULT_LOG_DIR,
                   help='Where to write the filled prompt, grok log, progress')
    p.add_argument('--upstream-url', default=os.environ.get(
        'YT_AI_UPSTREAM_URL', DEFAULT_UPSTREAM_URL))
    p.add_argument('--upstream-remote', default=os.environ.get(
        'YT_AI_UPSTREAM_REMOTE', DEFAULT_UPSTREAM_REMOTE))
    p.add_argument('--upstream-ref', default=os.environ.get(
        'YT_AI_UPSTREAM_REF', DEFAULT_UPSTREAM_REF))
    p.add_argument('--dry-run', action='store_true',
                   help='Fetch, write the prompt, do not invoke Grok')
    p.add_argument('--force', action='store_true',
                   help='Invoke Grok even if HEAD already contains upstream')
    p.add_argument('--no-fetch', action='store_true',
                   help='Do not git fetch (use the existing upstream remote ref)')
    p.add_argument('--no-commit', action='store_true',
                   help='Tell Grok not to commit (default: always commit)')
    p.add_argument('--timeout', type=int, default=3600,
                   help='Seconds for the Grok invocation (0 = no limit)')
    p.add_argument('--max-turns', type=int, default=120, help='Grok --max-turns')
    p.add_argument('--grok-bin', default=os.environ.get('GROK_BIN', 'grok'),
                   help='Grok executable')
    p.add_argument('--model', default=os.environ.get('GROK_MODEL', ''),
                   help='Optional grok --model')
    p.add_argument('--grok-arg', action='append', default=[],
                   help='Extra arg passed through to grok (repeatable)')
    p.add_argument('--incoming-limit', type=int, default=80,
                   help='Max incoming commit lines to embed in the prompt')
    return p.parse_args(argv)


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


def ensure_upstream_remote(name: str, url: str) -> None:
    proc = git(['remote', 'get-url', name])
    if proc.returncode != 0:
        eprint(f'Adding remote {name} -> {url}')
        git(['remote', 'add', name, url], check=True)
        return
    current = (proc.stdout or '').strip()
    if current.rstrip('/') != url.rstrip('/'):
        eprint(f'Updating remote {name}: {current} -> {url}')
        git(['remote', 'set-url', name, url], check=True)


def porcelain_blockers() -> list[str]:
    """Tracked modifications / merges that make a merge unsafe to start."""
    proc = git(['status', '--porcelain=v1', '-z'])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    blockers = []
    for entry in (proc.stdout or '').split('\0'):
        if not entry:
            continue
        # Rename lines: "R  old\0new" — treat as blocker.
        code = entry[:2]
        path = entry[3:]
        if code == '??':
            continue
        if code.strip() == '':
            continue
        blockers.append(f'{code} {path}')
    return blockers


def merge_in_progress() -> bool:
    return (REPO / '.git' / 'MERGE_HEAD').exists()


def truncate_lines(text: str, limit: int) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return '(none)'
    if limit and len(lines) > limit:
        hidden = len(lines) - limit
        lines = lines[:limit] + [f'… and {hidden} more']
    return '\n'.join(lines)


def names_only(diff_args: list[str]) -> list[str]:
    proc = git(diff_args)
    if proc.returncode != 0:
        return []
    return [ln for ln in (proc.stdout or '').splitlines() if ln.strip()]


def build_prompt(
    template: str,
    *,
    today: str,
    branch: str,
    head: str,
    upstream_remote: str,
    upstream_url: str,
    upstream_ref: str,
    upstream_short: str,
    incoming_log: str,
    overlap: str,
    upstream_deletes: str,
    do_commit: bool,
) -> str:
    if do_commit:
        commit_instruction = (
            '- Always git-commit the completed merge. Do not leave MERGE_HEAD. '
            'Do not ask. Do not push.'
        )
    else:
        commit_instruction = (
            '- Do **not** git commit, amend, or push. Leave the merge in the '
            'index / working tree for review. (Operator passed --no-commit.)'
        )
    replacements = {
        '__TODAY__': today,
        '__BRANCH__': branch,
        '__HEAD__': head,
        '__UPSTREAM_REMOTE__': upstream_remote,
        '__UPSTREAM_URL__': upstream_url,
        '__UPSTREAM_REF__': upstream_ref,
        '__UPSTREAM_SHORT__': upstream_short or '(unknown until fetch)',
        '__INCOMING_LOG__': incoming_log or '(none)',
        '__OVERLAP__': overlap or '(none)',
        '__UPSTREAM_DELETES__': upstream_deletes or '(none)',
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


def run_grok(cmd: list[str], log_file: Path, timeout: int) -> int:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    eprint('+', ' '.join(cmd[:6]), '…')
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
            )
        except FileNotFoundError:
            eprint(f'error: {cmd[0]!r} not found on PATH. Install grok or pass --grok-bin.')
            return 127

        def _kill(*_):
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

        old_int = signal.signal(signal.SIGINT, lambda *_: _kill())
        try:
            deadline = time.monotonic() + timeout if timeout else None
            assert proc.stdout is not None
            while True:
                if deadline is not None and time.monotonic() > deadline:
                    eprint(f'error: grok timed out after {timeout}s')
                    _kill()
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
        'STATUS: MERGED',
        'STATUS: UP_TO_DATE',
        'STATUS: BLOCKED',
        'STATUS: FAILED',
    ):
        if token in text:
            return token.split()[-1]
    return None


def append_progress(path: Path, rec: dict) -> None:
    import json
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def main(argv=None) -> int:
    args = parse_args(argv)
    if not PROMPT_TEMPLATE.is_file():
        eprint(f'error: prompt template not found: {PROMPT_TEMPLATE}')
        return 2
    if not (REPO / '.git').exists():
        eprint(f'error: not a git checkout: {REPO}')
        return 2

    args.log_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    stamp = time.strftime('%Y-%m-%dT%H%M%S')

    try:
        branch = git_out(['rev-parse', '--abbrev-ref', 'HEAD'])
        head = git_out(['rev-parse', 'HEAD'])
    except RuntimeError as exc:
        eprint(f'error: {exc}')
        return 2

    if branch == 'HEAD':
        eprint('error: detached HEAD; checkout master (or another branch) first')
        return 2

    if merge_in_progress() and not args.force:
        eprint('error: a merge is already in progress. Finish or abort it, or pass --force.')
        return 2

    blockers = porcelain_blockers()
    if blockers and not args.force:
        eprint('error: tracked working tree is dirty; refusing to merge:')
        for line in blockers[:30]:
            eprint('  ', line)
        eprint('Commit/stash these, or pass --force if Grok should try anyway.')
        return 2

    ensure_upstream_remote(args.upstream_remote, args.upstream_url)
    upstream_spec = f'{args.upstream_remote}/{args.upstream_ref}'

    if not args.no_fetch:
        eprint(f'Fetching {upstream_spec} …')
        fetch = git(['fetch', '--prune', args.upstream_remote, args.upstream_ref])
        if fetch.returncode != 0:
            eprint('error: git fetch failed:')
            eprint(fetch.stderr or fetch.stdout)
            return 1

    try:
        upstream_sha = git_out(['rev-parse', upstream_spec])
        upstream_short = git_out(['rev-parse', '--short', upstream_spec])
        merge_base = git_out(['merge-base', 'HEAD', upstream_spec])
    except RuntimeError as exc:
        eprint(f'error: {exc}')
        return 1

    try:
        incoming_n = int(git_out(['rev-list', '--count', f'HEAD..{upstream_spec}']))
    except (RuntimeError, ValueError):
        incoming_n = 0

    incoming_log = git_out([
        'log', '--oneline', '--no-merges', f'HEAD..{upstream_spec}',
    ])
    overlap_ours = set(names_only(['diff', '--name-only', f'{merge_base}..HEAD']))
    overlap_theirs = set(names_only(['diff', '--name-only', f'{merge_base}..{upstream_spec}']))
    overlap = sorted(overlap_ours & overlap_theirs)
    deletes = names_only(['diff', '--name-only', '--diff-filter=D', f'{merge_base}..{upstream_spec}'])
    our_kept_deletes = sorted(set(deletes) & overlap_ours) if deletes else []
    # Files they delete that still exist in HEAD, whether we touched them or not.
    still_present = []
    for path in deletes:
        if (REPO / path).exists():
            still_present.append(path)

    eprint(f'Branch:          {branch}')
    eprint(f'HEAD:            {head[:12]}')
    eprint(f'Upstream:        {upstream_short} ({upstream_spec})')
    eprint(f'Merge-base:      {merge_base[:12]}')
    eprint(f'Incoming:        {incoming_n} commit(s)')
    eprint(f'Overlapping:     {len(overlap)} file(s)')
    eprint(f'Upstream deletes still in tree: {len(still_present)}')

    up_to_date = incoming_n == 0
    if up_to_date and not args.force:
        eprint('Already up to date. Skipping Grok.')
        rec = {
            'status': 'UP_TO_DATE',
            'exit_code': 0,
            'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'head': head,
            'upstream': upstream_sha,
            'incoming': 0,
        }
        append_progress(args.log_dir / PROGRESS_NAME, rec)
        return 0

    template = PROMPT_TEMPLATE.read_text(encoding='utf-8')
    prompt = build_prompt(
        template,
        today=today,
        branch=branch,
        head=head,
        upstream_remote=args.upstream_remote,
        upstream_url=args.upstream_url,
        upstream_ref=args.upstream_ref,
        upstream_short=upstream_short,
        incoming_log=truncate_lines(incoming_log, args.incoming_limit),
        overlap=truncate_lines('\n'.join(overlap), 200),
        upstream_deletes=truncate_lines('\n'.join(still_present), 200),
        do_commit=not args.no_commit,
    )
    prompt_file = args.log_dir / f'prompt-{stamp}.txt'
    log_file = args.log_dir / 'grok' / f'{stamp}.log'
    prompt_file.write_text(prompt, encoding='utf-8')
    eprint(f'Wrote prompt: {prompt_file}')

    if args.dry_run:
        eprint('dry-run: would exec:', ' '.join(grok_cmd(args, prompt_file)[:8]), '…')
        return 0

    t0 = time.time()
    rc = run_grok(grok_cmd(args, prompt_file), log_file, args.timeout)
    elapsed = round(time.time() - t0, 1)
    status = parse_status_from_log(log_file)
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
        'upstream': upstream_sha,
        'incoming': incoming_n,
        'overlap': len(overlap),
        'log': str(log_file),
        'prompt': str(prompt_file),
    }
    try:
        rec['head_after'] = git_out(['rev-parse', 'HEAD'])
    except RuntimeError:
        rec['head_after'] = None
    append_progress(args.log_dir / PROGRESS_NAME, rec)
    eprint(f'-- status={status} exit={rc} elapsed={elapsed}s')
    eprint(f'Log: {log_file}')

    if rc == 130:
        return 130
    if status in ('MERGED', 'UP_TO_DATE') and rc == 0:
        return 0
    if status == 'BLOCKED':
        return 3
    return 1 if rc == 0 else rc


if __name__ == '__main__':
    raise SystemExit(main())
