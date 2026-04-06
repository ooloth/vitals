# Scan: Stale Docs

Find documentation that has fallen out of sync with the codebase.

"Documentation" means everything that describes intended system behaviour:
markdown files (`README.md`, `docs/**`, `CLAUDE.md`), inline code comments
and docstrings, and diagrams (Mermaid charts, ASCII art, tables embedded in
markdown).

## What to look for

1. **Implemented features described as planned** — phrases like "not yet
   implemented", "planned", "future work", or future tense describing
   something already present in the code
2. **Stale references** — file paths, function names, directory layouts,
   CLI flags, or commands that no longer exist or have moved
3. **Behavioral descriptions that contradict the code** — a doc says the
   system does X; the code does Y
4. **Missing coverage** — significant recently-added features with no
   documentation at all
5. **Contradictions between docs** — one doc says X, another says Y about
   the same thing
6. **Stale comments** — inline `#` comments or docstrings that describe
   code that was since changed or removed

## How to investigate

1. Run `git log --oneline -20` to identify what has changed recently —
   focus on code that docs might not yet reflect
2. Use the project context to identify which docs exist and what each covers
3. Read the relevant doc files; for each claim, Grep or Read the source to
   verify it is still accurate
4. Cross-reference docs against each other for contradictions

Stay grounded in real mismatches. Do not flag:
- Deliberate future-work sections clearly labelled as such (e.g. a "Phase 2"
  or "Planned" subsection in an architecture doc)
- Minor wording imprecision that does not mislead a reader
- Design-intent sections in architecture docs that are consistent with the
  codebase direction even if not yet fully implemented

Use the project context to understand which areas of docs to prioritise and
what is known to be in flux.

## Output format

Write your output as JSON to the file path provided by the coordinator.

Include `reflections` — a list of brief observations about this step: what
context was missing or ambiguous, what caused hesitation or retries, what
would have made this step faster or more accurate. Return `[]` if you have
nothing to add.

```json
{
  "findings": [
    {
      "file": "docs/architecture/harness-self-improvement.md",
      "section": "Components",
      "description": "one sentence: what is stale and why it matters",
      "severity": "high | medium | low",
      "sample": "the stale sentence or paragraph verbatim"
    }
  ],
  "reflections": []
}
```

If nothing stale is found, return `{ "findings": [], "reflections": [] }`.
