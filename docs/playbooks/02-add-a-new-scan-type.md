# Add a new scan type

1. Create `prompts/scans/<type>.md`. Follow the contract:
   - Instructions for what to look for and how to query the data source
   - Output format: JSON written to the file path provided by the coordinator
   - Schema: `{ "findings": [ { "pattern", "description", "severity", "sample" } ] }`

2. Add a scan block to each project in `projects.json` that should run this
   scan type. Include `normal`, `flag`, and `ignore` arrays calibrated for
   that project, plus any type-specific fields the prompt requires.

3. If the scan type needs new source-specific fields (e.g. a new log backend),
   add them to `projects.schema.json` as a new scan definition under `$defs`.

4. Run a dry-run scan to validate output quality before enabling for real:

   ```bash
   uv run python run.py scan <project-id> --type <type> --dry-run
   ```
