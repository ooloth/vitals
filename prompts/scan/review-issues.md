# Review Issues

Review drafted GitHub issues before posting.

## The four rules

**Rule 1 — Problem section includes a greppable snippet.**
Reject any issue that names a file path or line number as the primary way to
locate the problem without also including the verbatim code. The implementer
must be able to find the code by searching for it, not by trusting a stale
reference.

**Rule 2 — Definition of done is outside-in.**
Reject any proof point that describes what the code does rather than what you
observe when you run it. Each point must follow "run X, see Y." If a point
cannot be verified without reading the source, rewrite it.

**Rule 3 — Title names the problem, not the solution.**
Reject titles that prescribe an implementation (e.g. "Add check=True to
subprocess calls"). The title should make the problem legible to someone who
hasn't read the body.

**Rule 4 — One root cause per issue.**
Reject any issue that bundles two or more distinct root causes, or whose
definition of done would require changes in unrelated parts of the codebase.
Ask the drafter to split it — the drafter may return multiple issues from
what was one cluster. Each resulting issue must still pass all other rules.

## Additional checks

- **Problem**: one paragraph, explains why it matters — not just what it is.
- **Definition of done**: present and outside-in; not exhaustive, just key proof.
- **Out of scope**: present and specific — names what is intentionally excluded.
- **No duplication**: no two issues describe the same underlying problem.
- **Severity label**: matches the actual impact described in the body.

## Output format

Write your output as JSON to the file path provided by the coordinator.

Include `reflections` — a list of brief observations about this step: what context was missing or ambiguous, what caused hesitation or retries, what would have made this step faster or more accurate. Return `[]` if you have nothing to add.

If all issues pass:

```json
{
  "ready": true,
  "issues": [
    {
      "title": "...",
      "body": "...",
      "label": "..."
    }
  ],
  "reflections": []
}
```

If any issue fails:

```json
{
  "ready": false,
  "feedback": "most common failure across the set",
  "issues": [
    {
      "title": "...",
      "body": "...",
      "label": "...",
      "note": "which rule failed and why, for this specific issue"
    }
  ],
  "reflections": []
}
```
