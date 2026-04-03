# Draft Issues

Write GitHub issue drafts from triaged findings.

## Instructions

You will receive a JSON array of triaged clusters. For each cluster that warrants
a GitHub issue, write a clear, actionable issue with:

- A title that names the problem specifically (not "there are errors")
- A body that includes: what's happening, when it started, frequency, a sample
  log line, and a suggested next step
- A severity label: `sev:critical`, `sev:high`, `sev:medium`, `sev:low`

One cluster = one issue. Don't bundle unrelated problems.

## Output format

Respond with JSON only. No prose.

```json
{
  "issues": [
    {
      "title": "...",
      "body": "markdown body",
      "label": "sev:high"
    }
  ]
}
```
