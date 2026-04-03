# Scan: Log Error Spikes

Scan a project's logs for elevated error rates worth acting on.

## Instructions

Query the project's log source for the past 24 hours. Look for:

- **Error volume above threshold**: total error or fatal log count exceeding
  the normal baseline defined in the project context
- **Recurring error patterns**: a single error message or stack trace
  appearing many times — suggests a systematic problem, not a one-off
- **New error types**: error messages that did not appear in previous periods
  — higher priority than recurring known errors
- **Errors from unexpected sources**: services or components that don't
  normally log errors

Use the project context to filter known noise before reporting.

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
