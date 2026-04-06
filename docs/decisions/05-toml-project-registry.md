# TOML project registry

> **Superseded by [10-structured-scan-config-in-json.md](10-structured-scan-config-in-json.md)**

**Decision**: `projects/projects.json` is the single source of truth for
monitored projects and where their data lives.

**Why**: TOML is readable for hand-authoring, handles nested arrays of objects
cleanly, and avoids YAML's indentation sensitivity. Python 3.11+ has `tomllib`
built in — no extra dependency.

**Scope**: The registry holds non-secret config only. Secrets are referenced
as env var names injected at runtime via `op run`.
