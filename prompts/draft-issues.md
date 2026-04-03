# Draft Issues

Write GitHub issue drafts from triaged findings.

## Instructions

You will receive triaged clusters. For each cluster that warrants a GitHub
issue, write a clear, actionable issue using the structure below.

## Two rules that must hold for every issue

**1. Reference by snippet, never by location.**
Include the problematic code verbatim so the implementer can grep for it.
Never mention file paths or line numbers — they go stale the moment any
other issue is resolved.

**2. Acceptance criteria describe observable outcomes, not implementation choices.**
Each criterion must follow the pattern: "run X, observe Y." It should be
possible to verify the criterion without reading the code. Never prescribe
how to fix the problem — only describe what the world looks like when it
is fixed.

## Issue structure

```markdown
## Problem

<one paragraph: what is wrong and why it matters>

## Current behaviour

<code snippet of the problematic pattern — verbatim, greppable>

## Acceptance criteria

- [ ] <run X, observe Y>
- [ ] <run X, observe Y>
- [ ] Existing behaviour is unchanged: <describe the normal happy path and
      what a passing run looks like>

## Out of scope

<what not to change — protects the implementer from over-engineering and
the reviewer from scope creep>
```

## Output format

Write your output as JSON to the file path provided by the coordinator.

```json
{
  "issues": [
    {
      "title": "short, specific problem statement — not a solution",
      "body": "markdown body following the structure above",
      "label": "sev:critical | sev:high | sev:medium | sev:low"
    }
  ]
}
```

One cluster = one issue. Do not bundle unrelated problems.
