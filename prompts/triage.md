# Triage

Deduplicate and cluster raw scan findings into actionable groups.

## Instructions

You will receive a JSON array of raw findings from a log scan. Your job is to:

1. Merge findings that describe the same underlying problem
2. Discard findings that are noise (see project context)
3. Rank remaining findings by severity and frequency
4. Flag anything that looks new or worsening vs. a chronic background issue

## Output format

Respond with JSON only. No prose.

```json
{
  "clusters": [
    {
      "title": "short label for this problem",
      "count": 42,
      "first_seen": "ISO8601",
      "last_seen": "ISO8601",
      "severity": "critical | high | medium | low",
      "new": true,
      "worsening": false,
      "findings": ["pattern strings that were merged into this cluster"]
    }
  ]
}
```

If there is nothing actionable, return `{ "clusters": [] }`.
