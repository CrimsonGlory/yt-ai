#!/usr/bin/env python3
"""Add yt-dlp site-request extractors, one Grok session per domain.

Reads yt-dlp-site-requests-issues.csv for rows that are all of:

    yt_ai_supported=false
    registration_needed in {false, unknown}
    drm in {false, unknown}
    domain non-empty

For each matching domain (newest issue first; duplicates collapsed), launches
a **fresh** `grok -p` process with always-approve and a self-contained prompt.
Sequential by design. On success the agent commits, citing yt-dlp/yt-dlp#N.

Examples:

    # Smoke-test the first domain only
    python3 devscripts/add_site_requests.py --limit 1

    # Show what would run without calling Grok
    python3 devscripts/add_site_requests.py --dry-run --limit 5

    # Full batch (skips domains already FIXED/SKIPPED in the progress log)
    python3 devscripts/add_site_requests.py

    # Resume at a domain
    python3 devscripts/add_site_requests.py --start-at racingtv.com

    # One known issue
    python3 devscripts/add_site_requests.py --only hobune.stream
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CSV_PATH = REPO / 'yt-dlp-site-requests-issues.csv'
PROMPT_TEMPLATE = Path(__file__).resolve().parent / 'add_site_requests.prompt.md'
DEFAULT_LOG_DIR = REPO / 'tmp' / 'add-site-requests'
PROGRESS_NAME = 'progress.jsonl'

SAFE_DOMAIN = re.compile(r'[^a-zA-Z0-9._-]+')


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description='Iterate unmatched yt-dlp site-requests and add each with a fresh Grok session.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument('--csv', type=Path, default=CSV_PATH,
                   help='Path to yt-dlp-site-requests-issues.csv')
    p.add_argument('--log-dir', type=Path, default=DEFAULT_LOG_DIR,
                   help='Where to write prompts, logs, progress')
    p.add_argument('--limit', type=int, default=0, help='Handle at most N domains (0 = all)')
    p.add_argument('--offset', type=int, default=0, help='Skip the first N matching domains')
    p.add_argument('--start-at', metavar='DOMAIN', help='Skip domains until this one (inclusive)')
    p.add_argument('--only', metavar='DOMAIN_OR_ID', action='append', default=[],
                   help='Only these domains or github_issue_id values (repeatable, or comma-separated)')
    p.add_argument('--dry-run', action='store_true',
                   help='Print targets / write prompts, do not invoke Grok')
    p.add_argument('--no-resume', action='store_true',
                   help='Do not skip domains already marked FIXED/SKIPPED in the progress log')
    p.add_argument('--retry-failed', action='store_true',
                   help='Re-run domains whose last progress status was FAILED (default: skip them too)')
    p.add_argument('--stop-on-fail', action='store_true',
                   help='Abort the batch on the first Grok non-zero exit')
    p.add_argument('--no-commit', action='store_true',
                   help='Tell Grok not to git-commit (default: commit on success)')
    p.add_argument('--timeout', type=int, default=1800,
                   help='Seconds per Grok invocation (0 = no limit)')
    p.add_argument('--max-turns', type=int, default=120, help='Grok --max-turns')
    p.add_argument('--grok-bin', default=os.environ.get('GROK_BIN', 'grok'),
                   help='Grok executable')
    p.add_argument('--model', default=os.environ.get('GROK_MODEL', ''),
                   help='Optional grok --model')
    p.add_argument('--grok-arg', action='append', default=[],
                   help='Extra arg passed through to grok (repeatable)')
    return p.parse_args(argv)


def flag(v: str) -> str:
    return (v or '').strip().lower()


def is_target_row(row: dict) -> bool:
    if not (row.get('domain') or '').strip():
        return False
    if flag(row.get('yt_ai_supported')) != 'false':
        return False
    if flag(row.get('registration_needed')) not in ('false', 'unknown'):
        return False
    if flag(row.get('drm')) not in ('false', 'unknown'):
        return False
    return True


def load_targets(csv_path: Path) -> list[dict]:
    """Newest-first CSV; collapse duplicate domains, keep the newest issue as primary."""
    with csv_path.open(newline='', encoding='utf-8') as f:
        rows = [r for r in csv.DictReader(f) if is_target_row(r)]
    by_domain: dict[str, dict] = {}
    for row in rows:
        domain = row['domain'].strip()
        key = domain.lower()
        if key not in by_domain:
            rec = dict(row)
            rec['domain'] = domain
            rec['related_issue_ids'] = [row['github_issue_id']]
            by_domain[key] = rec
        else:
            by_domain[key]['related_issue_ids'].append(row['github_issue_id'])
    return list(by_domain.values())


def flatten_only(values: list[str]) -> set[str]:
    out = set()
    for v in values:
        for part in v.split(','):
            part = part.strip().lower()
            if part:
                out.add(part)
    return out


def slug(domain: str, issue_id: str) -> str:
    safe = SAFE_DOMAIN.sub('_', domain).strip('._') or 'site'
    return f'{issue_id}-{safe}'


def load_progress(path: Path) -> dict[str, str]:
    last: dict[str, str] = {}
    if not path.is_file():
        return last
    with path.open(encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            domain = rec.get('domain')
            status = rec.get('status')
            if domain and status:
                last[domain.lower()] = status
    return last


def append_progress(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def build_prompt(template: str, row: dict, today: str, do_commit: bool) -> str:
    issue_id = row['github_issue_id']
    related = row.get('related_issue_ids') or [issue_id]
    extras = [i for i in related if str(i) != str(issue_id)]
    related_fmt = ', '.join(f'yt-dlp/yt-dlp#{i}' for i in extras) if extras else '(none)'
    if do_commit:
        commit_instruction = (
            '- After a **successful** live byte-fetch (public URL, no login/DRM/Turnstile), '
            'git-add **only** the new extractor, `_extractors.py`, `supportedsites.md`, and '
            '`README.md` if you edited the New extractors list — then create a **single** commit:\n'
            f'  `[<ie_name>] Add extractor (yt-dlp/yt-dlp#{issue_id})`\n'
            '- Complete sentences are fine in the body; the subject must cite '
            f'`yt-dlp/yt-dlp#{issue_id}`. Do not `git add -A`. Do not amend. Do not push.\n'
            '- If you skipped, leave the tree clean (revert any partial files). Do not commit a skip.'
        )
    else:
        commit_instruction = (
            '- Do **not** git commit, amend, or push. Leave the working tree dirty for review. '
            '(Operator passed --no-commit.)'
        )
    replacements = {
        '__DOMAIN__': row['domain'],
        '__ISSUE_ID__': issue_id,
        '__RELATED_ISSUES__': related_fmt,
        '__ISSUE_TITLE__': (row.get('title') or '').replace('\n', ' '),
        '__ISSUE_STATUS__': row.get('status') or '',
        '__ISSUE_LABELS__': row.get('labels') or '',
        '__YT_AI_SUPPORTED__': row.get('yt_ai_supported') or '',
        '__REGISTRATION_NEEDED__': row.get('registration_needed') or '',
        '__DRM__': row.get('drm') or '',
        '__TODAY__': today,
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
        '--no-auto-update',
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
    for token in ('STATUS: FIXED', 'STATUS: SKIPPED', 'STATUS: FAILED'):
        if token in text:
            return token.split()[-1]
    return None


def matches_only(row: dict, only: set[str]) -> bool:
    if not only:
        return True
    domain = row['domain'].lower()
    issue = str(row['github_issue_id']).lower()
    if domain in only or issue in only:
        return True
    for rel in row.get('related_issue_ids') or []:
        if str(rel).lower() in only:
            return True
    return False


def select_targets(rows: list[dict], args, progress: dict[str, str]) -> list[dict]:
    only = flatten_only(args.only)
    selected = []
    started = args.start_at is None
    start_at = (args.start_at or '').lower()
    for row in rows:
        domain = row['domain']
        if only and not matches_only(row, only):
            continue
        if not started:
            if domain.lower() == start_at:
                started = True
            else:
                continue
        if not args.no_resume:
            last = progress.get(domain.lower())
            if last in ('FIXED', 'SKIPPED'):
                continue
            if last == 'FAILED' and not args.retry_failed:
                continue
        selected.append(row)
    if args.offset:
        selected = selected[args.offset:]
    if args.limit and args.limit > 0:
        selected = selected[:args.limit]
    return selected


def main(argv=None) -> int:
    args = parse_args(argv)
    if not args.csv.is_file():
        eprint(f'error: CSV not found: {args.csv}')
        return 2
    if not PROMPT_TEMPLATE.is_file():
        eprint(f'error: prompt template not found: {PROMPT_TEMPLATE}')
        return 2

    template = PROMPT_TEMPLATE.read_text(encoding='utf-8')
    today = date.today().isoformat()
    all_targets = load_targets(args.csv)
    args.log_dir.mkdir(parents=True, exist_ok=True)
    progress_path = args.log_dir / PROGRESS_NAME
    progress = load_progress(progress_path)
    targets = select_targets(all_targets, args, progress)

    eprint(f'Matching CSV domains: {len(all_targets)}')
    eprint(f'Selected this run: {len(targets)}  (log dir: {args.log_dir})')
    if not targets:
        eprint('Nothing to do.')
        return 0

    prompts_dir = args.log_dir / 'prompts'
    grok_dir = args.log_dir / 'grok'
    prompts_dir.mkdir(parents=True, exist_ok=True)
    grok_dir.mkdir(parents=True, exist_ok=True)

    stats = {'FIXED': 0, 'SKIPPED': 0, 'FAILED': 0, 'ERROR': 0}
    interrupted = False
    do_commit = not args.no_commit

    for i, row in enumerate(targets, 1):
        domain = row['domain']
        issue_id = row['github_issue_id']
        banner = f'[{i}/{len(targets)}] {domain}  (yt-dlp/yt-dlp#{issue_id})'
        eprint('\n' + '=' * 72)
        eprint(banner)
        eprint('=' * 72)

        prompt = build_prompt(template, row, today, do_commit)
        stem = slug(domain, issue_id)
        prompt_file = prompts_dir / f'{stem}.txt'
        prompt_file.write_text(prompt, encoding='utf-8')
        log_file = grok_dir / f'{stem}.log'

        if args.dry_run:
            eprint(f'dry-run: wrote {prompt_file}')
            eprint(f'dry-run: would exec: {" ".join(grok_cmd(args, prompt_file)[:8])} …')
            continue

        t0 = time.time()
        rc = run_grok(grok_cmd(args, prompt_file), log_file, args.timeout)
        elapsed = round(time.time() - t0, 1)
        status = parse_status_from_log(log_file)
        if rc == 130:
            interrupted = True
            status = status or 'ERROR'
        elif rc != 0 and not status:
            status = 'ERROR'
        elif not status:
            status = 'FAILED'
        stats[status] = stats.get(status, 0) + 1

        rec_out = {
            'domain': domain,
            'github_issue_id': issue_id,
            'status': status,
            'exit_code': rc,
            'elapsed_s': elapsed,
            'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'log': str(log_file),
        }
        append_progress(progress_path, rec_out)
        eprint(f'-- {domain}: status={status} exit={rc} elapsed={elapsed}s')

        if interrupted:
            eprint('Interrupted; remaining domains not started. Re-run to resume.')
            break
        if args.stop_on_fail and status in ('FAILED', 'ERROR'):
            eprint('--stop-on-fail: aborting batch')
            break

    eprint('\n' + '-' * 72)
    eprint('Done.', ' '.join(f'{k}={v}' for k, v in stats.items() if v) or 'dry-run')
    eprint(f'Progress: {progress_path}')
    if args.dry_run:
        return 0
    if interrupted:
        return 130
    return 0 if stats.get('ERROR', 0) == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
