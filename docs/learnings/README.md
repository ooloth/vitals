# Learnings

Discoveries made while running the loops — things that surprised us, things
that didn't work the way we expected, and adjustments made as a result.

---

## How this works (intended mechanics — not yet implemented)

Each learning is a dated observation about how agency behaves in practice:
what a prompt got wrong, where the coordinator broke, what signal looks like
in a real project. Not general programming knowledge — specific discoveries
from running these loops against real codebases.

**After each run**, a reflection step reads the run transcript and appends
new learnings to the relevant file here. Each entry is one or two lines,
dated, referencing the run that produced it.

**When a pattern repeats** — the same class of mistake appearing in three or
more learnings — it escalates. Repeated prompt failures become prompt rules.
Repeated coordinator bugs become coordinator rules in `docs/rules.md`.
Repeated calibration misses become conventions. The escalation is proposed
as a GitHub issue for human review before being applied; auto-generated
agent instructions have been shown to hurt performance when applied without
review.

**At the start of each run**, the coordinator injects relevant learnings into
the prompt so the agent benefits from past observations without accumulating
a growing context window over time.

---

## Format

```
- YYYY-MM-DD: one or two lines describing what was observed and what it
  implies. Reference the run or issue that surfaced it if possible.
```

Append only — do not edit or delete existing entries. If an earlier learning
turns out to be wrong, add a correction as a new entry rather than removing
the original. The history of being wrong is useful.
