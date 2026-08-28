You are working in the yt-dlp checkout at the current working directory.

Fix **one** broken live extractor test. Work only on this domain. Start a fresh investigation; do not assume anything from other sites.

## Target

- Domain: `{domain}`
- CSV row: `has_true_live_test={has_true_live_test}, confirmed_working_on_date={confirmed_working_on_date}, register_only={register_only}, cloudflare_turnstile={cloudflare_turnstile}`
- Known extractor IE names: `{extractors}`
- Current public byte-fetch test URLs:
```
{test_urls}
```

This domain already has a "true live test" (`_TESTS` case that is supposed to download media bytes: not `only_matching`, not `skip_download`/`simulate`, not a playlist, not a gone/404 skip). The live probe never succeeded (`confirmed_working_on_date` is NULL). The site was classified as public (no registration, no Cloudflare Turnstile). **The test is not working.**

Today's date: `{today}`

## Goal

Make at least one **true live byte-fetch** succeed for this domain:

1. Extract info from a currently available public URL on this site.
2. Download real media bytes (`yt-dlp --test` writes the first ~10KB). Empty extraction / simulate / skip_download does **not** count.
3. Leave a passing `_TESTS` case that future `python -m devscripts.run_tests ExtractorName` / `hatch test ExtractorName` can run.

## How to work

1. Locate the extractor(s) under `yt_dlp/extractor/` for `{domain}` (class names listed above). Read `_TESTS`, `_VALID_URL`, and `_real_extract`.
2. Reproduce the current failure:
   ```
   python3 -Werror -Xdev yt_dlp/__main__.py -v --test --retries 0 --extractor-retries 0 --socket-timeout 20 --no-playlist "<url>"
   ```
   and/or:
   ```
   python3 -m devscripts.run_tests <ExtractorName>
   ```
3. Diagnose. Typical causes, in order:
   - Sample URL is dead / 404 / geo / unpublished → find a **new currently public** video on the same site (browse the site, web search, check the homepage / recent videos). Same site and same extractor, not a random embed on another domain.
   - Site HTML/API changed → fix the extractor (selectors, API endpoints, headers, impersonate, `_VALID_URL`).
   - Stale `info_dict` / `md5` → update expected fields from a successful `--test` run.
   - Login / Turnstile / DRM / geo / site dead → only after you **proved** it with logs. Do not assume this from the CSV.
4. Apply the smallest fix that makes a live byte-fetch pass:
   - Update `_TESTS`: `url`, `md5` of the first 10241 bytes from `--test`, `info_dict` (`id` and `ext` are required; fill title and other fields the test reports).
   - Keep **at least one** true live byte-fetch test. Do not convert it to `only_matching`, `skip_download`, `simulate`, or playlist-only.
   - Old dead URLs may be kept as `skip: 'video gone'` (or similar) **in addition to** a new working test.
   - Follow `CONTRIBUTING.md` extractor conventions. Run `hatch fmt` or `ruff check --fix` on files you edit.
   - Do **not** add `# noqa` unless a maintainer would require it.
   - If you changed extractor **logic** (API, `_VALID_URL`, fallbacks, impersonate, expected errors) — not just `_TESTS` URLs / `md5` / `info_dict` / `skip` — add or revise a one-line bullet in `README.md` `# CHANGES FROM YT-DLP` (alphabetical extractor-fix list). Test-only refreshes do not need a README bullet. See `AGENTS.md`.
5. Verify by actually downloading with `--test` until media bytes are written. Re-run `python3 -m devscripts.run_tests <ExtractorName>` until it passes (or only fails on unrelated skipped cases).
6. Update `live-site-status.csv` for **this domain only**:
   - If a public byte-fetch succeeded: set `confirmed_working_on_date` to `{today}`. Leave `register_only=false` and `cloudflare_turnstile=false`.
   - If you proved the site is login-only: `register_only=true`, date stays `NULL`.
   - If you proved Cloudflare Turnstile: `cloudflare_turnstile=true`, date stays `NULL`.
   - If the site is gone / DRM-only / geo-blocked from here and you cannot find a public sample: leave the date `NULL` and add a precise `skip` reason on the test. Do not invent a fake pass.

## Constraints

- Touch only files needed for this domain (usually one extractor module, maybe `_extractors.py`, and the one CSV row). If extractor logic changed, also update `README.md` `# CHANGES FROM YT-DLP`.
- Do not "fix" by disabling the test unless you proved no public sample exists.
- Do not refactor unrelated extractors.
- Do not push.
{commit_instruction}

## When you are done

Print exactly this block (fill it in):

```
STATUS: FIXED | SKIPPED | FAILED
DOMAIN: {domain}
EXTRACTOR: <IE name>
URL: <url that works, or none>
BYTES: <size downloaded, or 0>
CSV: <what you wrote to live-site-status.csv>
NOTES: <one or two sentences: what was wrong and what you changed>
```
