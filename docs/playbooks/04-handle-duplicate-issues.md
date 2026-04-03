# Handle a scan that posts duplicate issues

The scan loop deduplicates by title against currently open issues. If a
duplicate slips through (e.g. the original was closed before the new scan ran):

1. Close the duplicate in GitHub manually.
2. Tighten the `ignore` array in the relevant scan block in `projects.json`
   to describe the pattern so future scans skip it.
