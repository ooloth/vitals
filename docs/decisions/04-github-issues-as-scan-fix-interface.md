# GitHub issues as the scan/fix interface

**Decision**: Scan posts GitHub issues; fix reads them. This is the only
coupling between the two loops.

**Why**: Scan and fix have different rhythms and different failure modes. A
direct coupling would require them to run together and fail together. GitHub
issues are inspectable, manually editable, and independent of both loops.
Either side can be replaced without touching the other.

**Labels**: Issues posted by scan carry a `sev:*` severity label, `autonomous`
and `needs-human-review` (applied to all agent-created issues), and a source
label (`scan:codebase`, `scan:logs`, or `scan:retrospective`). The fix loop picks
up issues via `gh issue list --label ready-for-agent` — the human-applied signal that
an issue has been reviewed and is ready to act on.
