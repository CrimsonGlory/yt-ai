You are working in the yt-ai checkout at the current working directory.

Add **one** new site extractor. Work only on this site. Start a fresh investigation; do not assume anything from other site-request sessions.

## Target

- Domain: `__DOMAIN__`
- yt-dlp issue: [yt-dlp/yt-dlp#__ISSUE_ID__](https://github.com/yt-dlp/yt-dlp/issues/__ISSUE_ID__)
- Related issues (same domain): `__RELATED_ISSUES__`
- Issue title: `__ISSUE_TITLE__`
- Issue status / labels: `__ISSUE_STATUS__` / `__ISSUE_LABELS__`
- CSV flags (pre-screen only, **re-verify live**): `yt_ai_supported=__YT_AI_SUPPORTED__, registration_needed=__REGISTRATION_NEEDED__, drm=__DRM__`

Today's date: `__TODAY__`

This domain is **not** in yt-ai's dedicated extractor list. The GitHub site-request is the source of example URLs and context. Fetch the issue (and comments if needed) with `gh`:

```
gh issue view __ISSUE_ID__ --repo yt-dlp/yt-dlp --comments
```

## Goal

If the site is publicly downloadable **and Generic cannot already download it**, add a working extractor and tests, then commit.

If it is not worth a custom extractor, skip. Do **not** invent a half-working extractor.

## Skip immediately (do not implement, do not commit)

Prove this with actual HTTP/extractor logs, then stop with `STATUS: SKIPPED`:

1. **Generic already works.** Before writing any extractor, run `--test` on a current public URL and confirm **real media bytes** are written while Generic (or another existing dedicated IE) handles it. If Generic can download the video, a custom extractor is pointless — skip. Metadata-only / `simulate` / empty formats do **not** count as Generic working.
2. **Registration / login / account / paid membership required** to play the media.
3. **DRM** (Widevine, FairPlay, PlayReady, SAMPLE-AES-only, “this video is DRM protected”, KnownDRM-style sites).
4. **Cloudflare Turnstile** (the interactive widget / `cf-turnstile` / challenge that impersonate cannot clear). A normal Cloudflare HTML challenge that **impersonate** solves is OK — keep going. Turnstile is not.
5. Site is gone, seized, empty, or has no remaining public media URL you can find.
6. yt-ai **already** has a dedicated extractor that handles these URLs (not Generic-only). If so, skip rather than duplicating.

Do **not** skip only because yt-dlp labeled the issue `wontfix` or `piracy/illegal`. This fork may still add the site, unless one of the skip reasons above is true.

## How to work

1. Open the issue and collect **currently playable public example URLs**. Prefer single videos. The issue URLs may be dead — if so, find a current public URL on the **same domain**.
2. **Probe with the current yt-ai extractors first** (Generic is the fallback). This is mandatory before any new code:
   ```
   python3 -Werror -Xdev yt_dlp/__main__.py -v --test --retries 0 --extractor-retries 0 --socket-timeout 20 --no-playlist "<url>"
   ```
   - If the log shows `[generic]` (or another existing IE) **and** `--test` writes media bytes (typically ~10241 bytes), Generic already works. **Do not implement a custom extractor.** `STATUS: SKIPPED` with `SKIP_REASON: generic-works`.
   - Falling back to Generic and then failing (`Unsupported URL`, no formats, 0 bytes) means Generic does **not** work — continue.
   - Note login / DRM / Turnstile if they appear.
3. If any skip reason is proven, stop. Do not write an extractor that only raises `login_required` or DRM, and do not add one when Generic already downloads the file.
4. If public media works in a browser (same IP, no account) **and Generic cannot download it**, implement a dedicated extractor:
   - Follow `CONTRIBUTING.md` **Adding support for a new site** and yt-ai coding conventions.
   - New file `yt_dlp/extractor/<name>.py` with class `…IE`, `_VALID_URL`, `_TESTS`, `_real_extract`.
   - Import it in `yt_dlp/extractor/_extractors.py` (class name must end with `IE`; keep the file's import style).
   - Use helpers from `yt_dlp/extractor/common.py` (`_download_webpage`, `_download_json`, `_extract_m3u8_formats_and_subtitles`, JWPlayer, JSON-LD, OpenGraph). Prefer stable APIs over brittle CSS.
   - Impersonate when a Cloudflare/WAF block is the only issue (not Turnstile).
   - NSFW sites must return `age_limit`.
   - Extraction of optional metadata must be non-fatal. `id` plus `url` or `formats` are mandatory.
5. Tests — at least one **true live byte-fetch** `_TESTS` case:
   - Not `only_matching`, not `skip_download` / `simulate`, not playlist-only.
   - `url` is a currently public video on this domain.
   - `md5` of the **first 10241 bytes** from `yt-dlp --test`.
   - `info_dict` must include `id` and `ext`; add other fields the test reports.
   - Extra URL shapes may be `only_matching`.
   - Run:
     ```
     python3 -m devscripts.run_tests <ExtractorName>
     ```
     and/or `hatch test <ExtractorName>` until it passes (or only fails on unrelated skips).
   - Confirm bytes on disk with `--test` (empty simulate does **not** count).
6. Docs (required if the extractor works):
   - Regenerate the supported-sites list:
     ```
     python3 devscripts/make_supportedsites.py supportedsites.md
     ```
   - Update `README.md` `# CHANGES FROM YT-DLP` **New extractors** with **one** alphabetical bullet for this IE, for example:
     `* **IE_NAME** (\`__DOMAIN__\`): <one-line approach>. Request: [yt-dlp/yt-dlp#__ISSUE_ID__](https://github.com/yt-dlp/yt-dlp/issues/__ISSUE_ID__)`
   - Do **not** put this under Extractor fixes. Do not leave the fork changelog stale. See `AGENTS.md`.
7. Format: `hatch fmt` or `ruff check --fix` on files you edited. No `# noqa` unless a maintainer would require it.

## Constraints

- Touch only files for **this** site: the new extractor, `_extractors.py`, `supportedsites.md`, and the **New extractors** README bullet.
- Do not refactor unrelated extractors. Do not “fix” other site-requests in this session.
- Do not push. Do not `git add -A`. Do not amend previous commits.
__COMMIT_INSTRUCTION__

## When you are done

Print exactly this block (fill it in):

```
STATUS: FIXED | SKIPPED | FAILED
DOMAIN: __DOMAIN__
ISSUE: yt-dlp/yt-dlp#__ISSUE_ID__
EXTRACTOR: <IE name, or none>
URL: <public url that works, or none>
BYTES: <size downloaded with --test, or 0>
SKIP_REASON: <generic-works | login | drm | turnstile | dead | already-supported | none>
COMMIT: <hash or none>
NOTES: <one or two sentences>
```
