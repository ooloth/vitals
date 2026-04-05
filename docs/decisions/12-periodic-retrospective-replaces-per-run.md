# Periodic retrospective replaces per-run retrospective agent

**Decision**: Cross-run pattern detection runs as a standard scan
(`agency/retrospective`) triggered periodically, not as an agent call at the
end of every run.

**Why**: The per-run retrospective had three structural problems:

1. **Wrong granularity.** A single run rarely reveals a pattern — one
   non-convergence could be a bad prompt, a flaky model response, or a
   genuinely hard input. Cross-run patterns require reading multiple runs.
   An end-of-run agent call has access to exactly one run's data.

2. **No quality gate.** Calling the agent inline meant its output was used
   immediately — no review step, no draft→review pipeline. Issues could be
   posted based on a single observation that a reviewer would have caught and
   rejected.

3. **Bloated run cost.** An extra agent call at the end of every scan or fix
   run added latency and API cost whether or not there was anything useful to
   say. Most runs don't have actionable patterns.

**Replacement design**: Each run writes its own data to `.logs/` (metadata,
reflections, and per-step transcripts). A periodic scan reads across recent
runs, detects patterns, and routes findings through the standard
find→triage→draft→review pipeline. This means:

- Pattern detection spans as many runs as needed
- Draft quality is checked by the review agent before posting
- No per-run overhead — the retrospective only runs when scheduled

**Boundary**: The per-run data capture (transcript writes, reflections in
step outputs, metadata on exit) is still mechanical and per-run. Only the
*analysis* step moved to periodic.
