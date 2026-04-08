# Handle a scan that posts duplicate issues

The scan loop runs a semantic dedup step before posting. It compares each
candidate issue against all open issues (title and body) using the agent's
own judgment and decides whether to post, comment on an existing issue, or
skip.

If a duplicate still slips through (e.g. the dedup step misjudges overlap,
or the original was closed before the new scan ran):

1. Close the duplicate in GitHub manually.
2. Tighten the `ignore` array in the relevant scan block in `projects.json`
   to describe the pattern so future scans skip it.
