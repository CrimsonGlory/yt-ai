You are working in the yt-ai git checkout at the current working directory.

The daily full test suite (`make test`) failed. Fix **every listed failing test** (and lint, if that is what failed), and **commit each independent fix separately**. Do not wait for a human. Do not push.

Today's date: __TODAY__
Current branch: `__BRANCH__`
Current HEAD: `__HEAD__`
Test command: `__TEST_CMD__`
Test exit code: `__TEST_EXIT__`

## Suite result

Summary line from the log:

```
__SUMMARY_LINE__
```

Counts: failed=__FAILED_COUNT__, errors=__ERROR_COUNT__, passed=__PASSED_COUNT__, skipped=__SKIPPED_COUNT__, duration=__DURATION__

Full pytest / `make test` log (read this file if you need a traceback):
`__PYTEST_LOG__`

JUnit XML (may be missing if pytest crashed before writing it):
`__JUNIT_XML__`

Last lines of the log:

```
__LOG_TAIL__
```

## Failing tests

__FAILED_TESTS__

## Failure excerpts

__FAILURE_EXCERPTS__

## Goal

1. Make every listed failure pass (or, only if you **proved** it cannot pass from this environment, skip it with a precise reason — see below).
2. Re-run **only** the failing nodeids / extractor tests. Do **not** re-run `make test` / the full suite — it takes ~3 hours. Tomorrow's cron will.
3. Commit **each independent fix as its own commit** (usually one commit per extractor). Never one combined daily-test commit. Never push.

If the suite already has **zero** pytest failures and this is a `codetest` (ruff / autopep8) failure, fix the lint and commit that as `[daily-test] Fix lint`.

If you cannot reproduce a failure (transient network / 5xx / timeout) after **two** retries of that single test, leave that test alone and note it as remaining. Do not skip a test just because it flaked once.

## How to work

### 0. Safety

- Stay on `__BRANCH__`. Do not checkout a new branch. Do not rebase. Do not `reset --hard`. Do not `git add -A` (the tree has untracked media dumps).
- Do not push. Do not amend published commits.
- Do not commit downloaded videos, `*.mp4`, `*.m3u8`, `*.ts`, `*.dump`, logs, or anything under `tmp/`.
- This tree still supports **Python 3.10**. Do not drop 3.10.
- Never add DRM circumvention, credential-stealing, or supply-chain surprises.
- Follow `AGENTS.md` and `CONTRIBUTING.md`. If you change extractor **logic** (API, `_VALID_URL`, fallbacks, impersonate, expected errors) — not just `_TESTS` URLs / `md5` / `info_dict` / `skip` — add or revise a one-line bullet in `README.md` `# CHANGES FROM YT-DLP` (alphabetical extractor-fix list). Test-only refreshes do not need a README bullet.

### 1. Classify each failure

Work through the list **one independent fix at a time**. After a re-run passes, **commit that fix** (section 4) before starting the next failure. Typical buckets:

| Kind | What to do |
| --- | --- |
| Unit / CLI / networking / core (`test/test_*.py` other than download) | Real bug. Fix the code or the assertion. Do not skip. |
| `codetest` / ruff / autopep8 | `hatch fmt` or `ruff check --fix` on the files you touch; fix remaining lint by hand. |
| Download test, stale `md5` / `info_dict` | Re-run `--test` on a current public URL and update expected fields. Keep a true live byte-fetch. |
| Download test, dead / 404 / unpublished URL | Find a **new currently public** URL on the **same site / same extractor**. Keep the old case as `skip: 'video gone'` *in addition to* a working test — never instead of one. |
| Download test, extractor broken (selectors, API, headers) | Fix `_real_extract` / `_VALID_URL` / impersonate / fallbacks. Smallest change that makes `--test` write media bytes. |
| Login / account / paid / Cloudflare Turnstile / DRM / geo / site dead | Only after you **proved** it with logs. Then `skip:` with a precise reason. Do not invent a fake pass. Do not delete the extractor. |
| Hung / killed / no pytest summary | Diagnose from the log tail. If a single test hung, fix or time-box that extractor; do not ignore it. |

Do **not** "fix" by converting a true live byte-fetch into `only_matching` / `skip_download` / `simulate` unless you proved no public sample exists.

### 2. Reproduce one failure

Pytest nodeid:

```
python3 -m pytest -Werror --tb=short "<nodeid>"
```

Extractor download tests (`test/test_download.py::TestDownload::test_<Name>`):

```
python3 -m devscripts.run_tests <ExtractorName>
python3 -Werror -Xdev yt_dlp/__main__.py -v --test --retries 0 --extractor-retries 0 --socket-timeout 20 --no-playlist "<url>"
```

`--test` must write real media bytes (~10KB). Empty extraction / simulate does **not** count.

### 3. Apply the smallest fix, then re-run that test

- Follow `CONTRIBUTING.md` extractor conventions (fallbacks, `traverse_obj`, `fatal=False` for optional metadata).
- `id` + `url`/`formats` are mandatory; `age_limit` on NSFW.
- Run `hatch fmt` or `ruff check --fix` on files you edit. No `# noqa` unless a maintainer would require it.
- Update `live-site-status.csv` for a domain **only** if you actually changed that confirmation while fixing a live test.
- Then commit this fix (section 4) before touching the next failure.

### 4. Commit after each independent fix

__COMMIT_INSTRUCTION__

## Constraints

- Touch only files needed for these failures.
- Do not refactor unrelated extractors.
- Do not re-run the full suite.
- Do not push.
- A PARTIAL result (some tests fixed and committed, some remaining) is acceptable. An empty commit is not. A combined catch-all commit is not.

## When you are done

Print exactly this block (fill it in):

```
STATUS: FIXED | PARTIAL | FAILED | BLOCKED
FIXED: <comma-separated nodeids or extractor names now passing, or none>
REMAINING: <comma-separated still-failing nodeids, or none>
COMMITS: <comma-separated shas, or none>
NOTES: <2-5 sentences: what was wrong, what you changed, what you left>
```
