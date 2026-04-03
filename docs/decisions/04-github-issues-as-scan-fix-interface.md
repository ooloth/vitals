# GitHub issues as the scan/fix interface

**Decision**: Scan posts GitHub issues; fix reads them. This is the only
coupling between the two loops.

**Why**: Scan and fix have different rhythms and different failure modes. A
direct coupling would require them to run together and fail together. GitHub
issues are inspectable, manually editable, and independent of both loops.
Either side can be replaced without touching the other.

**Labels**: Issues posted by scan carry a `sev:*` label for severity and an
`agent` label so the fix loop can find them via `gh issue list --label agent`.
