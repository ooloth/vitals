# Review Issues

Review drafted GitHub issues before posting.

## Instructions

You will receive a JSON array of drafted issues. For each issue, check:

- **Title**: specific, names the actual problem, under 72 characters
- **Body**: includes what/when/how often/sample/next step — nothing missing
- **Label**: matches actual severity
- **Duplication**: no two issues describe the same problem
- **Actionability**: would a developer know what to investigate?

If all issues pass, mark ready. If any need improvement, return feedback and
the issues with inline notes so they can be rewritten.

## Output format

Respond with JSON only. No prose.

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

If not ready:

```json
{
  "ready": false,
  "feedback": "overall note on what needs fixing",
  "issues": [
    {
      "title": "...",
      "body": "...",
      "label": "...",
      "note": "specific fix needed for this issue, if any"
    }
  ]
}
```
