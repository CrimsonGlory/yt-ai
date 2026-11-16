#!/usr/bin/env python3
"""Fix unconfirmed public live extractor tests, one Grok session per domain.

Reads live-site-status.csv for rows:

    has_true_live_test=true, confirmed_working_on_date=NULL,
    register_only=false, cloudflare_turnstile=false

For each matching domain, launches a **fresh** `grok -p` process with
always-approve (full tool permissions) and a self-contained prompt so the
agent context stays clean. Sequential by design.

Examples:

    # Smoke-test the first domain only
    python3 devscripts/fix_unconfirmed_live_tests.py --limit 1

    # Show what would run without calling Grok
    python3 devscripts/fix_unconfirmed_live_tests.py --dry-run --limit 3

    # Full batch, skipping domains already recorded as done
    python3 devscripts/fix_unconfirmed_live_tests.py

    # Resume at a given domain
    python3 devscripts/fix_unconfirmed_live_tests.py --start-at allocine.fr
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import signal
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CSV_PATH = REPO / 'live-site-status.csv'
PROMPT_TEMPLATE = Path(__file__).resolve().parent / 'fix_unconfirmed_live_tests.prompt.md'
DEFAULT_LOG_DIR = REPO / 'tmp' / 'fix-unconfirmed-live-tests'
PROGRESS_NAME = 'progress.jsonl'

TARGET_FILTER = {
    'has_true_live_test': 'true',
    'confirmed_working_on_date': 'NULL',
    'register_only': 'false',
    'cloudflare_turnstile': 'false',
}


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description='Iterate unconfirmed public live tests and fix each with a fresh Grok session.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument('--csv', type=Path, default=CSV_PATH, help='Path to live-site-status.csv')
    p.add_argument('--log-dir', type=Path, default=DEFAULT_LOG_DIR, help='Where to write prompts, logs, progress')
    p.add_argument('--limit', type=int, default=0, help='Fix at most N domains (0 = all)')
    p.add_argument('--offset', type=int, default=0, help='Skip the first N matching domains')
    p.add_argument('--start-at', metavar='DOMAIN', help='Skip domains until this one (inclusive)')
    p.add_argument('--only', metavar='DOMAIN', action='append', default=[],
                   help='Only these domains (repeatable, or comma-separated)')
    p.add_argument('--dry-run', action='store_true', help='Print targets / write prompts, do not invoke Grok')
    p.add_argument('--no-resume', action='store_true',
                   help='Do not skip domains already marked FIXED/SKIPPED in the progress log')
    p.add_argument('--retry-failed', action='store_true',
                   help='Re-run domains whose last progress status was FAILED (default: skip them too)')
    p.add_argument('--stop-on-fail', action='store_true', help='Abort the batch on the first Grok non-zero exit')
    p.add_argument('--commit', action='store_true',
                   help='Tell Grok to git-commit the files for this domain after a successful fix')
    p.add_argument('--timeout', type=int, default=1500, help='Seconds per Grok invocation (0 = no limit)')
    p.add_argument('--max-turns', type=int, default=100, help='Grok --max-turns')
    p.add_argument('--grok-bin', default=os.environ.get('GROK_BIN', 'grok'), help='Grok executable')
    p.add_argument('--model', default=os.environ.get('GROK_MODEL', ''), help='Optional grok --model')
    p.add_argument('--grok-arg', action='append', default=[], help='Extra arg passed through to grok (repeatable)')
    p.add_argument('--no-inventory', action='store_true',
                   help='Do not load extractor inventory (prompt will only contain the domain)')
    return p.parse_args(argv)


def boolish(v: str) -> str:
    return (v or '').strip().lower()


def is_target_row(row: dict) -> bool:
    date_v = (row.get('confirmed_working_on_date') or '').strip()
    if date_v in ('', 'null', 'none', 'NULL', 'None'):
        date_v = 'NULL'
    return (
        boolish(row.get('has_true_live_test')) == 'true'
        and date_v == 'NULL'
        and boolish(row.get('register_only')) == 'false'
        and boolish(row.get('cloudflare_turnstile')) == 'false'
    )


def load_targets(csv_path: Path) -> list[dict]:
    with csv_path.open(newline='', encoding='utf-8') as f:
        return [row for row in csv.DictReader(f) if row.get('domain') and is_target_row(row)]


def flatten_only(values: list[str]) -> set[str]:
    out = set()
    for v in values:
        for part in v.split(','):
            part = part.strip().lower()
            if part:
                out.add(part)
    return out


def load_progress(path: Path) -> dict[str, str]:
    """Return domain -> last recorded STATUS."""
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
                last[domain] = status
    return last


def append_progress(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def load_inventory() -> dict:
    """Best-effort extractor inventory keyed by domain."""
    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / 'devscripts'))
    try:
        from live_site_status import inventory  # type: ignore
    except Exception as exc:
        eprint(f'warning: could not import live_site_status.inventory: {exc}')
        return {}
    eprint('Loading extractor inventory (once)…')
    return inventory()


def format_urls(urls: list[str], limit: int = 8) -> str:
    if not urls:
        return '(none recorded)'
    lines = [f'- {u}' for u in urls[:limit]]
    if len(urls) > limit:
        lines.append(f'- … and {len(urls) - limit} more')
    return '\n'.join(lines)


def build_prompt(template: str, row: dict, rec: dict | None, today: str, do_commit: bool) -> str:
    rec = rec or {}
    extractors = rec.get('extractors') or []
    urls = rec.get('public_urls') or []
    if do_commit:
        commit_instruction = (
            '- After a successful live byte-fetch, git-add **only** the extractor file(s) '
            'you changed, the one CSV row if you edited it, and `README.md` if you changed '
            'extractor logic (see AGENTS.md) — then create a single commit:\n'
            f"  `[{row['domain']}] Fix live extractor test`\n"
            '- Do not `git add -A`. Do not amend. Do not push.'
        )
    else:
        commit_instruction = '- Do **not** git commit, amend, or push. Leave the working tree dirty for review.'

    return template.format(
        domain=row['domain'],
        has_true_live_test=row.get('has_true_live_test', 'true'),
        confirmed_working_on_date=row.get('confirmed_working_on_date', 'NULL'),
        register_only=row.get('register_only', 'false'),
        cloudflare_turnstile=row.get('cloudflare_turnstile', 'false'),
        extractors=', '.join(extractors) if extractors else '(unknown — search yt_dlp/extractor for this domain)',
        test_urls=format_urls(urls),
        today=today,
        commit_instruction=commit_instruction,
    )


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

        # Propagate Ctrl-C to the grok process group.
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


def select_targets(rows: list[dict], args, progress: dict[str, str]) -> list[dict]:
    only = flatten_only(args.only)
    selected = []
    started = args.start_at is None
    start_at = (args.start_at or '').lower()
    for row in rows:
        domain = row['domain']
        if only and domain.lower() not in only:
            continue
        if not started:
            if domain.lower() == start_at:
                started = True
            else:
                continue
        if not args.no_resume:
            last = progress.get(domain)
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

    eprint(f'Matching CSV rows: {len(all_targets)}')
    eprint(f'Selected this run: {len(targets)}  (log dir: {args.log_dir})')
    if not targets:
        eprint('Nothing to do.')
        return 0

    inventory = {} if args.no_inventory else load_inventory()

    prompts_dir = args.log_dir / 'prompts'
    grok_dir = args.log_dir / 'grok'
    prompts_dir.mkdir(parents=True, exist_ok=True)
    grok_dir.mkdir(parents=True, exist_ok=True)

    stats = {'FIXED': 0, 'SKIPPED': 0, 'FAILED': 0, 'ERROR': 0}
    interrupted = False

    for i, row in enumerate(targets, 1):
        domain = row['domain']
        banner = f'[{i}/{len(targets)}] {domain}'
        eprint('\n' + '=' * 72)
        eprint(banner)
        eprint('=' * 72)

        rec = (inventory or {}).get(domain) or {}
        prompt = build_prompt(template, row, rec, today, args.commit)
        prompt_file = prompts_dir / f'{domain}.txt'
        prompt_file.write_text(prompt, encoding='utf-8')
        log_file = grok_dir / f'{domain}.log'

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
            # Grok exited 0 but did not print the STATUS block.
            status = 'FAILED'
        stats[status] = stats.get(status, 0) + 1

        rec_out = {
            'domain': domain,
            'status': status,
            'exit_code': rc,
            'elapsed_s': elapsed,
            'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'log': str(log_file),
            'extractors': rec.get('extractors') or [],
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
    eprint('Done.', ' '.join(f'{k}={v}' for k, v in stats.items() if v))
    eprint(f'Progress: {progress_path}')
    if args.dry_run:
        return 0
    if interrupted:
        return 130
    return 0 if stats.get('ERROR', 0) == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
