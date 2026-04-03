# No web UI, no API, no database

**Decision**: This is a terminal tool. It reads files, calls `claude -p`,
and posts to GitHub. Nothing else.

**Why**: A rendering layer adds no analytical value. An LLM can interpret raw
or lightly aggregated data and surface findings directly. The operational
simplicity — run from cron, inspect via `gh issue list` — is a feature. Any
server component changes the deployment model, adds auth requirements, and
creates infrastructure to maintain.
