# Panels

A panel is a question + a data source + a renderer.

Each panel type has a fixed `type` identifier, one or more supported data sources, and a typed params shape per source.

---

## `errors`

**Question**: What errors are occurring, how frequently, and is the situation improving or worsening?

**Display**: Errors grouped by type/message with occurrence counts, delta vs previous period, first seen / last seen timestamps.

### Supported sources

#### `google_cloud_logging`

```toml
[[projects.panels]]
type = "errors"
source = "google_cloud_logging"

[projects.panels.params]
project_id = "${GCP_PROJECT_ID}"
log_name = "projects/my-project/logs/app"   # optional filter
# severity filter defaults to ERROR and above
```

#### `grafana_loki`

```toml
[[projects.panels]]
type = "errors"
source = "grafana_loki"

[projects.panels.params]
datasource_uid = "${GRAFANA_DATASOURCE_UID}"
selector = '{app="my-api", env="prod"}'
# level filter defaults to error/ERROR
```

#### `axiom` (planned)

```toml
[[projects.panels]]
type = "errors"
source = "axiom"

[projects.panels.params]
dataset = "${AXIOM_DATASET}"
# field mappings TBD
```

#### `logfire` (planned)

TBD

---

## Future panel types (ideas)

- `deployments` — recent deploy history, success/failure rate, who deployed what
- `latency` — p50/p95/p99 response times, trend over time
- `uptime` — is it up? recent downtime incidents
- `usage` — active users, requests/min, growth trends
- `cost` — cloud spend, anomaly detection
- `db_health` — slow queries, connection pool exhaustion, table sizes
- `background_jobs` — queue depth, failure rate, processing lag
