# Scan: Log Anomalies

Scan a project's logs for unusual patterns that fall outside normal behaviour.

## Instructions

Query the project's log source for the past 24 hours. Look for:

- **Volume spikes**: total log volume significantly above the normal baseline
  for this time of day or day of week
- **Silence**: a service or component that normally produces logs has gone
  quiet — could indicate a crash or deployment failure
- **New log patterns**: messages or fields that have not appeared before,
  suggesting a code path that wasn't previously exercised
- **Latency outliers**: requests or jobs that took significantly longer than
  the normal baseline, even if they succeeded
- **Unexpected traffic patterns**: request rates, geographic distribution, or
  user behaviour that deviates from the norm

Use the project context to calibrate what counts as normal before reporting.
Anomalies are not necessarily errors — they are unexpected deviations from
the established baseline.

## How to query

### Axiom (APL)

```apl
['<dataset>']
| where _time > ago(24h)
| summarize count() by bin(_time, 1h)
| order by _time asc
```

```apl
['<dataset>']
| where _time > ago(24h)
| summarize count() by message
| order by count_ desc
| take 50
```

### Google Cloud Logging

```bash
gcloud logging read 'timestamp>="<24h-ago>"' \
  --project=<project-id> \
  --limit=500 \
  --format=json
```

## Output format

Write your output as JSON to the file path provided by the coordinator.

```json
{
  "findings": [
    {
      "pattern": "brief description of the anomaly",
      "count": 42,
      "first_seen": "ISO8601",
      "last_seen": "ISO8601",
      "severity": "error | warning | anomaly",
      "sample": "one representative log line or metric value"
    }
  ]
}
```

If there is nothing to flag, return `{ "findings": [] }`.
