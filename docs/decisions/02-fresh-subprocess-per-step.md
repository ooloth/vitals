# Fresh subprocess per step

**Decision**: Each agent step runs as a `claude -p` subprocess. No step
reuses a running session.

**Why**: A single session accumulates context across steps. The implementer
should not see the scan output; the reviewer should not see the implementation
history. Each agent gets exactly what the coordinator passes — nothing more.
Context contamination degrades quality in ways that are hard to diagnose.
