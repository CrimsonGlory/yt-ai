You are working in the yt-ai git checkout at the current working directory.

Pull the latest **yt-dlp** upstream into this fork, keep yt-ai compatible with upstream, resolve overlapping site work using the better (more future-proof) fix, and **always commit** the result. Do not wait for a human to commit.

Today's date: __TODAY__
Current branch: `__BRANCH__`
Current HEAD: `__HEAD__`
Upstream remote: `__UPSTREAM_REMOTE__` → `__UPSTREAM_URL__`
Upstream ref: `__UPSTREAM_REF__`

## What this fork is

yt-ai is **yt-dlp plus more**. Same architecture, same `yt_dlp` package, same CLI behavior — with:

- **More sites supported** (including extractors upstream marked "currently broken" that we restored because the site still publishes media).
- **Better support in general**: working live byte-fetch tests, extra URL patterns, fallbacks, extra metadata.
- **Fork identity**: user-facing name `yt-ai`, repo `CrimsonGlory/yt-ai`, binaries `yt-ai` / `yt-ai.exe`. Internal module remains `yt_dlp`. `pyproject.toml` keeps the `yt-dlp` script entry *and* adds `yt-ai`.

Stay **compatible with upstream**: take their core, networking, downloader, YouTube, and new extractors. Do not drift into a hard-to-merge fork. Do not drop our extra sites or weaken extractors to match a smaller upstream.

## Goal

1. Fetch `yt-dlp/yt-dlp` master.
2. Merge it into the current branch (`git merge --no-ff --no-commit`, then you commit).
3. On every overlapping site fix, **compare** both implementations and keep the one more likely to survive the next site change — or hybridize them.
4. Always create a git commit if anything was merged or resolved. Never leave a merge in progress. Never push.

If there is nothing new on upstream, print the STATUS block with `UP_TO_DATE` and stop. Do **not** create an empty commit.

## Snapshot (script-provided; re-fetch anyway)

Incoming commits (`HEAD..upstream`):
```
__INCOMING_LOG__
```

Files both sides touched since the merge-base (review these even if git auto-merges):
```
__OVERLAP__
```

Files upstream would delete that we still have:
```
__UPSTREAM_DELETES__
```

## How to work

### 0. Safety

- Stay on `__BRANCH__`. Do not checkout a new branch. Do not rebase. Do not `reset --hard`. Do not `git add -A` (the tree has untracked media dumps).
- Do not push. Do not amend published commits. Do not change git remotes other than ensuring the upstream remote exists.
- Do not commit downloaded videos, `*.mp4`, `*.m3u8`, `*.ts`, logs, or anything under `tmp/`.
- If tracked files are already dirty in a way that blocks a merge, stop with `STATUS: BLOCKED` and explain. Untracked media is fine.
- This tree still supports **Python 3.10**. Do not take "drop 3.10" / "remove compat" cleanups that break 3.10.
- Never take DRM circumvention, credential-stealing, or supply-chain surprises.

### 1. Remotes and fetch

```
git remote add upstream https://github.com/yt-dlp/yt-dlp.git   # if missing
git fetch --prune upstream
git rev-parse --short HEAD
git rev-parse --short upstream/__UPSTREAM_REF__
git merge-base HEAD upstream/__UPSTREAM_REF__
git log --oneline --no-merges HEAD..upstream/__UPSTREAM_REF__
git diff --stat HEAD...upstream/__UPSTREAM_REF__
```

If `HEAD` already contains `upstream/__UPSTREAM_REF__`, you are up to date. Stop.

### 2. Merge without committing yet

```
git merge --no-ff --no-commit upstream/__UPSTREAM_REF__
```

- If git refuses (local tracked changes, existing merge): fix only if it is a leftover merge you can complete safely; otherwise `STATUS: BLOCKED`.
- `--no-commit` is required so you can review auto-merged extractors **before** the merge commit.

### 3. Resolve conflicts and overlapping site work

Process **conflicted files first**, then overlapping extractors that merged cleanly.

**Brand / fork-identity files** (keep yt-ai names, port functional upstream edits):

- `README.md`, `CONTRIBUTING.md`, `Maintainers.md`, `Makefile`
- `pyproject.toml` (keep `yt-ai` script entry and CrimsonGlory URLs; take real dependency/build changes)
- `.github/**` issue templates, `FUNDING.yml`, workflow names that mention the project
- User-facing strings in `yt_dlp/options.py`, `yt_dlp/update.py`, `yt_dlp/plugins.py`, `test/test_config.py`

If upstream changed *behavior* in those files, apply the behavior on top of yt-ai branding. Do not revert the rename commit.

**Core / downloader / networking / postprocessor / utils / YouTube:**

- Default to **upstream**. Compatibility matters most here.
- Keep a local patch only if it is a proven bugfix upstream does not have, and it still applies.

**Changelog.md / supportedsites.md / README fork changelog:**

- Changelog: keep both sides, chronological. New upstream version headers stay. Do not rewrite history. Do not regenerate the whole file.
- `supportedsites.md`: after extractor resolution, regenerate with `python3 devscripts/make_supportedsites.py supportedsites.md`. We must not lose sites we still support.
- `README.md` `# CHANGES FROM YT-DLP` is the **fork changelog** (what yt-ai does differently from yt-dlp). After the merge, update it: add remaining fork-only extractor/behavior diffs, drop bullets that upstream now has, keep branding and restored-site bullets. See `AGENTS.md`.

**Extractors (`yt_dlp/extractor/`):** this is the important part.

#### 3a. Classification

For each overlapping or conflicted extractor, classify:

| Case | Action |
| --- | --- |
| Upstream-only new site / new file | **Take upstream.** |
| Ours-only extra site | **Keep ours.** Make sure `_extractors.py` still imports it. |
| Upstream deleted as dead / "currently broken" | **Do not delete blindly.** If the site still publishes public media (quick homepage/search check), keep our extractor. If the site is gone, DRM-only, or the domain is parked, accept the deletion. |
| Both sides changed the same extractor | **Compare. Pick the more future-proof fix, or hybridize.** See rubric. |
| Tests-only change | Keep every **true live byte-fetch** test we have. Add their new tests. Dead sample URLs may be `skip: 'video gone'` *in addition to* a working test — never instead of one. |

#### 3b. Rubric: which site fix is better?

Prefer the implementation **more likely to survive the next site change**, not the one that happens to work on today's HTML snapshot.

Score **higher**:

1. Public / documented JSON API, stable `__NEXT_DATA__` / Nuxt / Next payload, or first-party player config — over CSS selectors and full-page regex.
2. **Fallback chain**: API → page JSON → HTML, not a single path.
3. `traverse_obj`, `*_or_none`, `fatal=False` for optional metadata. Mandatory fields stay `id` + `url`/`formats` (and `age_limit` on porn).
4. Stable identifiers (API field names, media ids) over minified JS names, hashed CSS classes, or one-off query strings.
5. Broader `_VALID_URL` / URL types without becoming a greedy generic.
6. Extra metadata that is non-fatal to extract.
7. A `_TESTS` case that actually downloads media bytes (`yt-dlp --test` / `yt-ai --test`), not only `only_matching` / `skip_download` / `simulate`.
8. Follows `CONTRIBUTING.md` extractor conventions (fallbacks, collapse fallbacks, convenience parsers).

Score **lower**:

1. One brittle regex on the whole HTML.
2. `meta['key']` chains that throw if a key vanishes.
3. Drops URL patterns we already handle.
4. Turns a working live test into `skip` / `only_matching`.
5. Marks the IE broken while the site still serves media.
6. Requires login for content that is still public, without proof.

**Usual winner is a hybrid:**

- Take the more robust extraction core (often upstream's API rewrite, sometimes ours).
- Keep our extra `_VALID_URL` branches, embed handling, extra metadata, and true live tests.
- Keep their new URL patterns and tests too.

Do **not** concatenate both `_real_extract` bodies. Produce one coherent extractor.

#### 3c. How to compare in git

During a merge:

- ours: `git show :2:path` (or `HEAD:path`)
- theirs: `git show :3:path` (or `upstream/__UPSTREAM_REF__:path`)
- base: `git show :1:path`

If the merge has not started, use `HEAD:path` vs `upstream/__UPSTREAM_REF__:path`.

When the site is public and a test URL exists, **empiricism beats guessing**:

```
python3 -Werror -Xdev yt_dlp/__main__.py -v --test --retries 0 --extractor-retries 0 --socket-timeout 20 --no-playlist "<url>"
```

If taking upstream breaks a live fetch that ours still passes, keep ours (or hybrid) unless upstream is clearly the right long-term API and the failure is just a dead sample URL.

Time-box live checks. Prioritize:

1. Conflicted extractors
2. Overlapping extractors
3. High-churn sites (YouTube, Twitter/X, TikTok, Instagram) — default upstream unless our diff is a clear extra
4. Extractors they deleted

Skip live tests for login-only / geo / Cloudflare Turnstile sites; compare on code quality then.

### 4. `_extractors.py`

Keep imports for every extractor we still ship. Respect the parenthesized import + trailing-comma style. Do not drop restored IEs because upstream's `_extractors.py` no longer lists them.

### 5. Sanity checks

After the tree looks right:

- `python3 -m compileall -q yt_dlp`
- `hatch fmt` (or `ruff check --fix`) on files **you** edited, not the whole repo if that rewrites unrelated upstream style.
- Do not add `# noqa` unless a maintainer would require it.
- A full extractor test run is out of scope. If you changed a public overlapping extractor and have a URL, one `--test` is enough.

### 6. Commit (mandatory)

If the merge produced any change, **you must commit**. This is not optional. Do not leave `MERGE_HEAD` around. Do not ask for confirmation.

Stage **only** merge results and your resolution edits:

```
git add -u -- yt_dlp devscripts test bundle .github CONTRIBUTING.md Changelog.md README.md Makefile pyproject.toml supportedsites.md Maintainers.md
```

If that path list misses a resolved file, add that file by name. Never `git add -A`. Never add media.

Commit **once** to conclude the merge (`git commit` with no `--amend`):

```
[upstream] Merge yt-dlp master (__UPSTREAM_SHORT__)

- Take: <short list of upstream changes you accepted>
- Keep ours: <extractors / files where our fix is more future-proof>
- Hybrid: <extractors combined>
- Deleted by upstream, kept: <sites still alive>
- Accepted deletions: <sites actually dead>
```

If git already opened a merge commit template, replace it with the message above. Include the upstream short SHA (`__UPSTREAM_SHORT__` after fetch).

If you had to finish the merge commit first and then still needed extractor tweaks, a **second** commit is OK:

```
[upstream] Prefer more future-proof extractors after merge
```

Do not push. Do not create tags. Do not bump a release unless upstream's merge already did via `version.py` / `Changelog.md`.

__COMMIT_INSTRUCTION__

## Constraints

- Compatible with upstream: core stays theirs unless we have a unique proven fix.
- Superset of sites: we support everything they do, plus more, unless a site is truly gone.
- Better support: never "resolve" by deleting tests or marking a live site broken.
- Always commit a completed merge.
- Never push.

## When you are done

Print exactly this block (fill it in):

```
STATUS: MERGED | UP_TO_DATE | BLOCKED | FAILED
UPSTREAM: <short sha, or none>
MERGE: <merge commit sha, or none>
TAKE: <comma-separated extractors/areas taken from upstream>
KEEP: <comma-separated extractors we kept>
HYBRID: <comma-separated extractors combined>
DROPPED_DELETES: <upstream deletions we refused>
NOTES: <2-5 sentences: what came in, hard conflicts, why you preferred a side>
```
