# CLAUDE.md Ordering

Order sections in CLAUDE.md most-stable-first. LLM providers cache prompt
prefixes — the more stable the beginning of a file, the more cache hits it
generates across conversations, reducing latency and cost.

## Recommended order

1. **Identity / role** — what this project is, what the agent's role is here
2. **Rules and invariants** — things that never change
3. **Architecture** — how the system is structured
4. **Commands** — how to run checks, tests, and the loops
5. **Known issues** — temporary workarounds currently in place
6. **Temporary notes** — ephemeral context for the current session

Stable rules at the top, volatile notes at the bottom.

## What to avoid

Don't put frequently-changing content at the top of CLAUDE.md. Every edit
to that content busts the cache for everything below it. Session-specific
notes, current task context, and recent decisions belong at the bottom —
or not in CLAUDE.md at all.
