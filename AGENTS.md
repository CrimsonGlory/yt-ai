# yt-ai agent rules

## Fork changelog

After any change that is a **difference from upstream yt-dlp**, update the
`# CHANGES FROM YT-DLP` section in `README.md` as part of the same work (or at
the end of a related batch). Do not leave that section stale.

That README section is the **fork changelog**: what yt-ai does differently from
yt-dlp. It is not `Changelog.md`, which is the yt-dlp-style release log.

Update it for:

- New extractors, restored extractors, and extractor logic / URL / API /
  fallback / impersonate changes
- User-visible behavior, branding, defaults, internals, and developer workflow
- Expected errors users will see (site shut down, app-only, geo, login)

Do **not** add a per-site bullet for test-only work (new sample URL, `md5` /
`info_dict` refresh, `skip` reason, `live-site-status.csv`). Summarize those
under **Testing and developer workflow**.

How to write extractor bullets:

- One line, extractor name in `**ie_name**`, describing the approach (API,
  fallback, impersonate), not the symptom
- Keep the extractor-fix list alphabetical
- If an extractor is already listed, revise that line instead of duplicating it
