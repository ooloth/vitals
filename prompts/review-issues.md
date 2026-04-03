# Review Issues

Review drafted GitHub issues before posting.

## The two rules

Every issue must satisfy both rules before it is ready:

**Rule 1 — No location references.**
Reject any issue that mentions file paths, line numbers, or module names
as the primary way to locate the problem. The issue must include a code
snippet that can be grepped for. A reviewer should be able to find the
relevant code without trusting a stale reference.

**Rule 2 — AC describes observable outcomes only.**
Reject any acceptance criterion that prescribes an implementation detail
(e.g. "use check=True", "add a try/except", "extract a shared module").
Every criterion must follow "run X, observe Y" — a concrete action and
its expected result. If a criterion cannot be verified by running
something and observing the outcome, rewrite it.

## Additional checks

- **Title**: names the problem specifically, not the solution. Under 72 chars.
- **Problem**: one paragraph, explains why it matters — not just what it is.
- **Current behaviour**: includes a verbatim code snippet of the bad pattern.
- **Scope boundary**: "Out of scope" section is present and meaningful.
- **No duplication**: no two issues describe the same underlying problem.

## Output format

Write your output as JSON to the file path provided by the coordinator.

If all issues pass both rules and all checks:

```json
{
  "ready": true,
  "issues": [
    {
      "title": "...",
      "body": "...",
      "label": "..."
    }
  ]
}
```

If any issue fails:

```json
{
  "ready": false,
  "feedback": "overall note on the most common failure",
  "issues": [
    {
      "title": "...",
      "body": "...",
      "label": "...",
      "note": "specific failure for this issue — which rule and why"
    }
  ]
}
```
