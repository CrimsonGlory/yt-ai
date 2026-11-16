#!/usr/bin/env python3
"""Build and refresh live-site-status.csv.

A "true live test" is an extractor _TESTS case that downloads media bytes
from a live URL (not only_matching, not skip_download, not a gone/404 skip).
Login-gated cases still count as having a live test (register_only=true).

confirmed_working_on_date is set to today when a public live byte-fetch
succeeds, left as the previous date if it now fails, and empty (NULL) when
there is no true live test or the domain has never passed.
"""

from __future__ import annotations

import csv
import os
import re
import sys
import tempfile
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from yt_dlp.extractor import gen_extractors
from yt_dlp.extractor.generic import GenericIE

CSV_FIELDS = (
    'domain',
    'has_true_live_test',
    'confirmed_working_on_date',
    'register_only',
    'cloudflare_turnstile',
)
CSV_PATH = Path(__file__).resolve().parent.parent / 'live-site-status.csv'
TODAY = date.today().isoformat()

MULTI_PART_TLDS = {
    'ac.uk', 'co.uk', 'gov.uk', 'ltd.uk', 'me.uk', 'net.uk', 'org.uk', 'plc.uk', 'sch.uk',
    'com.au', 'net.au', 'org.au', 'edu.au', 'gov.au',
    'co.jp', 'ne.jp', 'or.jp', 'ac.jp', 'go.jp',
    'co.kr', 'or.kr', 'go.kr', 'ac.kr',
    'com.br', 'net.br', 'org.br', 'gov.br',
    'co.nz', 'net.nz', 'org.nz', 'govt.nz', 'ac.nz',
    'co.za', 'org.za', 'gov.za', 'ac.za',
    'com.mx', 'org.mx', 'gob.mx',
    'co.in', 'net.in', 'org.in', 'ac.in', 'gov.in', 'res.in',
    'com.tr', 'org.tr', 'gov.tr',
    'com.tw', 'org.tw', 'gov.tw', 'edu.tw',
    'com.hk', 'org.hk', 'gov.hk', 'edu.hk',
    'com.sg', 'org.sg', 'gov.sg', 'edu.sg',
    'co.id', 'or.id', 'go.id', 'ac.id',
    'com.ar', 'org.ar', 'gov.ar',
    'com.co', 'org.co', 'gov.co',
    'com.pe', 'org.pe', 'gob.pe',
    'co.il', 'org.il', 'gov.il', 'ac.il',
    'com.ua', 'org.ua', 'gov.ua',
    'com.cn', 'org.cn', 'gov.cn', 'net.cn', 'edu.cn', 'ac.cn',
    'co.th', 'ac.th', 'go.th', 'or.th',
    'com.my', 'org.my', 'gov.my', 'edu.my',
    'com.ph', 'org.ph', 'gov.ph',
    'com.pk', 'org.pk', 'gov.pk', 'edu.pk',
    'com.ng', 'org.ng', 'gov.ng', 'edu.ng',
    'com.eg', 'org.eg', 'gov.eg',
    'com.sa', 'org.sa', 'gov.sa',
    'com.vn', 'org.vn', 'gov.vn',
    'com.pl', 'org.pl', 'gov.pl',
}

LOGIN_RE = re.compile(
    r'\b(login|log[\s-]?in|account|cookie|netrc|auth(?:entication|orization)?|'
    r'password|premium|subscription|adobe\s*pass|credentials?|logged[\s-]?in|'
    r'patron-only|members?\s+only)\b',
    re.I,
)
GONE_RE = re.compile(
    r'\b(404|not found|no longer available|video gone|video was removed|'
    r'invalid url|does not exist|expired|removed|dead|offline|not available|'
    r'livestream has ended|live might have ended|gone)\b',
    re.I,
)
TURNSTILE_RE = re.compile(
    r'turnstile|cf-chl|challenge-platform|cf-mitigated|cf-turnstile|'
    r'challenges\.cloudflare\.com',
    re.I,
)


def root_domain(host: str) -> str:
    host = (host or '').lower().split(':')[0].strip('.')
    if host.startswith('www.'):
        host = host[4:]
    if not host or host in ('localhost',) or re.fullmatch(r'\d+\.\d+\.\d+\.\d+', host):
        return host
    parts = host.split('.')
    if len(parts) >= 3 and '.'.join(parts[-2:]) in MULTI_PART_TLDS:
        return '.'.join(parts[-3:])
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return host


def url_domain(url: str) -> str | None:
    if not url or not isinstance(url, str):
        return None
    if '://' not in url:
        return None
    try:
        host = urlparse(url).hostname
    except Exception:
        return None
    if not host:
        return None
    return root_domain(host)


def skip_text(test: dict) -> str:
    s = test.get('skip')
    return s if isinstance(s, str) else ''


def is_byte_fetch_test(test: dict) -> bool:
    """Whether this case is designed to download media bytes from a live URL."""
    if test.get('only_matching'):
        return False
    if test.get('expected_exception'):
        return False
    params = test.get('params') or {}
    if params.get('skip_download') or params.get('simulate'):
        return False
    if any(k.startswith('playlist') for k in test):
        return False
    info = test.get('info_dict') or {}
    if info.get('_type') in ('playlist', 'url', 'url_transparent'):
        return False
    if not info.get('id') or not info.get('ext'):
        return False
    url = test.get('url') or ''
    if not url.startswith('http'):
        return False
    return True


def is_login_gated(test: dict, ie) -> bool:
    text = skip_text(test)
    if text and LOGIN_RE.search(text) and not GONE_RE.search(text):
        return True
    return False


def inspect_extractor_source(ie) -> bool:
    try:
        src = Path(inspect_file(ie)).read_text(errors='replace')
    except Exception:
        return False
    return bool(TURNSTILE_RE.search(src))


def inspect_file(ie) -> str:
    import inspect
    return inspect.getsourcefile(type(ie)) or ''


def bool_csv(v: bool) -> str:
    return 'true' if v else 'false'


def null_date(v: str | None) -> str:
    return v or 'NULL'


def load_existing(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    out = {}
    with path.open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row.get('domain'):
                out[row['domain']] = row
    return out


def inventory():
    """Group extractors by domain and classify live tests."""
    domains: dict[str, dict] = {}

    def bucket(domain: str) -> dict:
        rec = domains.get(domain)
        if rec is None:
            rec = {
                'domain': domain,
                'public_urls': [],
                'login_urls': [],
                'has_true_live_test': False,
                'register_only': False,
                'cloudflare_turnstile': False,
                'extractors': [],
            }
            domains[domain] = rec
        return rec

    for ie in gen_extractors():
        if isinstance(ie, GenericIE) or ie.IE_DESC is False:
            continue
        src_turnstile = inspect_extractor_source(ie)
        tests = list(ie.get_testcases(include_onlymatching=True))
        domain_from_tests = None
        for t in tests:
            d = url_domain(t.get('url') or '')
            if d:
                domain_from_tests = d
                break
        if not domain_from_tests:
            # Fall back to first http-looking string in VALID_URL, else IE name
            m = re.search(r'([a-z0-9-]+(?:\.[a-z0-9-]+)+)', getattr(ie, '_VALID_URL', '') or '', re.I)
            domain_from_tests = root_domain(m.group(1)) if m else ie.IE_NAME

        rec = bucket(domain_from_tests)
        rec['extractors'].append(ie.IE_NAME)
        if src_turnstile:
            rec['cloudflare_turnstile'] = True

        for t in tests:
            if not is_byte_fetch_test(t):
                continue
            gone = bool(GONE_RE.search(skip_text(t)))
            login = is_login_gated(t, ie)
            if gone and not login:
                continue
            rec['has_true_live_test'] = True
            url = t['url']
            if login:
                rec['login_urls'].append(url)
            else:
                rec['public_urls'].append(url)

    for rec in domains.values():
        rec['register_only'] = bool(rec['has_true_live_test'] and not rec['public_urls'] and rec['login_urls'])
        # de-dupe URLs, keep order
        rec['public_urls'] = list(dict.fromkeys(rec['public_urls']))
        rec['login_urls'] = list(dict.fromkeys(rec['login_urls']))

    return domains


def _probe_one(url: str, outdir: str) -> dict:
    """Worker: fetch ~10KB of media from url. Must be top-level for pickling."""
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError, ExtractorError

    params = {
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'test': True,
        'simulate': False,
        'skip_download': False,
        'writeinfojson': False,
        'writedescription': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'retries': 0,
        'extractor_retries': 0,
        'fragment_retries': 0,
        'file_access_retries': 0,
        'socket_timeout': 20,
        'outtmpl': os.path.join(outdir, '%(id)s.%(ext)s'),
        'fixup': 'never',
        'overwrites': True,
        'cachedir': False,
        'noplaylist': True,
        'format': 'b/bv/w',
        'ignore_no_formats_error': False,
        'skip_unavailable_fragments': True,
        'consoletitle': False,
        'verbose': False,
    }
    result = {
        'ok': False,
        'turnstile': False,
        'error': '',
        'bytes': 0,
        'id': '',
        'url': url,
    }
    try:
        with YoutubeDL(params) as ydl:
            info = ydl.extract_info(url, download=True)
        if not info:
            result['error'] = 'empty info'
            return result
        result['id'] = str(info.get('id') or '')
        # Locate downloaded file
        size = 0
        for name in os.listdir(outdir):
            path = os.path.join(outdir, name)
            if os.path.isfile(path) and not name.endswith('.json'):
                size = max(size, os.path.getsize(path))
        # Also count in-memory requested bytes: test mode writes ~10KB
        if size <= 0:
            # Some extractors return a direct url without going through FD
            # if no formats; treat presence of formats+id as incomplete.
            fmts = info.get('formats') or []
            if info.get('url') or fmts:
                result['error'] = 'extracted but no media bytes written'
            else:
                result['error'] = 'no formats'
            return result
        result['bytes'] = size
        result['ok'] = size > 0
        return result
    except Exception as e:
        msg = f'{type(e).__name__}: {e}'
        result['error'] = msg[:400]
        blob = msg + '\n' + traceback.format_exc()
        if TURNSTILE_RE.search(blob):
            result['turnstile'] = True
        return result


def run_live(domains: dict, existing: dict, workers: int = 8, max_urls_per_domain: int = 2) -> dict:
    jobs = []
    tmp_root = tempfile.mkdtemp(prefix='yt-live-')
    for domain, rec in sorted(domains.items()):
        if rec['register_only'] or not rec['public_urls']:
            continue
        for i, url in enumerate(rec['public_urls'][:max_urls_per_domain]):
            outdir = os.path.join(tmp_root, re.sub(r'[^a-z0-9._-]+', '_', domain) + f'_{i}')
            os.makedirs(outdir, exist_ok=True)
            jobs.append((domain, url, outdir))

    print(f'Live-probing {len(jobs)} public byte-fetch URLs across '
          f'{len({d for d,_,_ in jobs})} domains with {workers} workers', flush=True)

    passed: dict[str, bool] = {}
    turnstile: dict[str, bool] = {}
    errors: dict[str, str] = {}

    firsts, rest_by_domain = [], {}
    seen = set()
    for domain, url, outdir in jobs:
        if domain not in seen:
            firsts.append((domain, url, outdir))
            seen.add(domain)
        else:
            rest_by_domain.setdefault(domain, []).append((url, outdir))

    from concurrent.futures import FIRST_COMPLETED, wait as fut_wait

    with ProcessPoolExecutor(max_workers=workers) as ex:
        pending = {}
        for domain, url, outdir in firsts:
            pending[ex.submit(_probe_one, url, outdir)] = domain

        done_n = 0
        total_est = len(firsts)
        while pending:
            finished, _ = fut_wait(pending, return_when=FIRST_COMPLETED, timeout=90)
            if not finished:
                # one hung worker: mark remaining oldest as timeout is hard; keep waiting
                continue
            for fut in finished:
                domain = pending.pop(fut)
                done_n += 1
                try:
                    r = fut.result(timeout=1)
                except Exception as e:
                    r = {'ok': False, 'turnstile': False, 'error': f'worker: {e}', 'bytes': 0}
                if r.get('ok'):
                    passed[domain] = True
                    rest_by_domain.pop(domain, None)
                    print(f'[{done_n}] OK {domain} ({r.get("bytes")} bytes)', flush=True)
                else:
                    errors[domain] = r.get('error') or 'fail'
                    print(f'[{done_n}] FAIL {domain}: {errors[domain][:140]}', flush=True)
                    nxt = rest_by_domain.get(domain) or []
                    if nxt:
                        nurl, ndir = nxt.pop(0)
                        pending[ex.submit(_probe_one, nurl, ndir)] = domain
                if r.get('turnstile'):
                    turnstile[domain] = True
            # checkpoint CSV every 25 domains so a kill still leaves dates
            if done_n % 25 == 0:
                write_csv(CSV_PATH, domains, existing, {
                    'passed': passed, 'turnstile': turnstile, 'errors': errors,
                })
                print(f'    checkpoint {CSV_PATH} passed={sum(passed.values())}', flush=True)

    return {'passed': passed, 'turnstile': turnstile, 'errors': errors}


def write_csv(path: Path, domains: dict, existing: dict, live: dict | None):
    live = live or {'passed': {}, 'turnstile': {}, 'errors': {}}
    rows = []
    for domain in sorted(domains):
        rec = domains[domain]
        prev = existing.get(domain) or {}
        has = rec['has_true_live_test']
        register_only = rec['register_only']
        turnstile = rec['cloudflare_turnstile'] or bool(live['turnstile'].get(domain))
        prev_date = (prev.get('confirmed_working_on_date') or '').strip()
        if prev_date in ('NULL', 'None', 'null'):
            prev_date = ''

        err = (live.get('errors') or {}).get(domain) or ''
        if err and LOGIN_RE.search(err):
            register_only = True

        if not has:
            confirmed = ''
        elif live['passed'].get(domain):
            confirmed = TODAY
        elif register_only:
            confirmed = prev_date
        elif domain in live['passed'] or domain in live['errors']:
            confirmed = prev_date
        else:
            confirmed = prev_date

        rows.append({
            'domain': domain,
            'has_true_live_test': bool_csv(has),
            'confirmed_working_on_date': null_date(confirmed),
            'register_only': bool_csv(register_only),
            'cloudflare_turnstile': bool_csv(turnstile),
        })

    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return rows


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    run = '--inventory-only' not in argv
    workers = 6
    for a in argv:
        if a.startswith('--workers='):
            workers = int(a.split('=', 1)[1])

    print('Building extractor inventory…', flush=True)
    domains = inventory()
    existing = load_existing(CSV_PATH)
    n_live = sum(1 for r in domains.values() if r['has_true_live_test'])
    n_pub = sum(1 for r in domains.values() if r['public_urls'])
    n_login = sum(1 for r in domains.values() if r['register_only'])
    print(f'Domains: {len(domains)}; with true live test: {n_live}; '
          f'public: {n_pub}; register_only: {n_login}', flush=True)

    live = None
    if run:
        live = run_live(domains, existing, workers=workers)
        print(f'Passed this run: {sum(1 for v in live["passed"].values() if v)}', flush=True)

    rows = write_csv(CSV_PATH, domains, existing, live)
    n_conf = sum(1 for r in rows if r['confirmed_working_on_date'])
    print(f'Wrote {CSV_PATH} ({len(rows)} rows, {n_conf} confirmed dates)', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
