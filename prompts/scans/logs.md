# Scan: Logs

Scan a project's logs for errors and anomalies worth acting on.

## Instructions

Query the project's log source for the past 24 hours. Look for:

- **Errors**: anything at `error` or `fatal` level
- **Warnings**: spikes or new patterns at `warn` level
- **Anomalies**: sudden volume increases, new error types, recurring failures
- **Silence**: services that normally log but have gone quiet

Use the project context to distinguish signal from noise before reporting.

## How to query

### Axiom (APL)

```apl
['<dataset>']
| where level in ("error", "ERROR", "fatal", "FATAL")
| where _time > ago(24h)
| summarize count(), min(_time), max(_time) by message
| order by count_ desc
```

### Google Cloud Logging

```bash
gcloud logging read 'severity>=ERROR' \
  --project=<project-id> \
  --freshness=24h \
  --limit=100 \
  --format=json
```

### Grafana Loki

```logql
{app="<app-label>"} |= "error" | pattern `<_> level=<level> <_> msg=<msg>`
```

## Output format

Write your output as JSON to the file path provided by the coordinator.

```json
{
  "findings": [
    {
      "pattern": "brief description of the error pattern",
      "count": 42,
      "first_seen": "ISO8601",
      "last_seen": "ISO8601",
      "severity": "error | warning | anomaly",
      "sample": "one representative log line"
    }
  ]
}
```

If there is nothing to flag, return `{ "findings": [] }`.
