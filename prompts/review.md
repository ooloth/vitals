# Review

Review an implementation before opening a PR.

## Instructions

You will receive an implementation summary and should review the actual diff.
Check:

- Does it solve what the issue asked for — nothing more, nothing less?
- Do tests pass?
- Are there obvious regressions or side effects?
- Is the PR title and body clear?

If approved, say so. If not, give specific, actionable feedback so the
implementer knows exactly what to fix.

## Output format

Write your output as JSON to the file path provided by the coordinator.

```json
{
  "approved": true,
  "feedback": ""
}
```

If not approved:

```json
{
  "approved": false,
  "feedback": "specific description of what needs to change"
}
```
