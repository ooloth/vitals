# Design Decisions

Decisions made during initial planning, with rationale.

---

## Static dashboard over periodic report

**Decision**: Build a web dashboard, not a scheduled text/markdown report.

**Why**: The primary value of this tool is aggregation + deduplication (e.g. "42 instances of this error type"). A flat report hits a ceiling quickly as data sources and question types grow. A dashboard with sidebar navigation scales naturally — each new question is a new route, not a new section in a linear document.

**Tradeoff**: More upfront effort than a cron + email digest. Accepted because the dashboard is the product.

---

## Config-driven panel/project model

**Decision**: Projects and panels are declared in `vitals.config.toml`. The app reads config at runtime; no UI needed to add a project initially.

**Why**: Decouples "what to show" from "how to show it". Adding a project requires no code changes. The config schema is also the future form schema for UI-based onboarding.

**Evolution**: Long-term, a UI onboarding flow generates the same TOML structure. The app never needs to distinguish hand-authored from UI-generated config.

---

## TOML for config

**Decision**: `vitals.config.toml` over YAML or JSON.

**Why**: TOML handles arrays of objects (projects + panels) more cleanly than YAML. Avoids YAML's indentation sensitivity and surprising parse behavior (unquoted strings, boolean edge cases). JSONC was considered but TOML is more readable for hand-authoring.

---

## Discriminated union for panel/source config

**Decision**: `source` is the discriminant field in panel config, mapped to typed params per source.

**Why**: Different log providers (GCP Logging, Grafana Loki, Axiom, Logfire) require different params. A discriminated union gives compile-time safety and makes the fetcher registry straightforward: `source` → fetch function.

**Example**:
```ts
type ErrorsPanelConfig =
  | { type: "errors"; source: "grafana_loki"; params: GrafanaLokiParams }
  | { type: "errors"; source: "google_cloud_logging"; params: GCLParams }
```

---

## 1Password via `op run` (not SDK)

**Decision**: Secrets injected as env vars via `op run --env-file=secrets.env -- next dev`. App reads `process.env` only.

**Why**: App is completely decoupled from 1Password. No SDK dependency. Secrets never touch disk. Portable — can swap 1Password for `.env` or any other secret manager without touching app code.

**Local setup**: `secrets.env` (gitignored) maps env var names to `op://` paths. `vitals.config.toml` references env var names.

---

## SQLite for historical snapshots

**Decision**: Store each panel's query result with a timestamp in SQLite.

**Why**: Enables trend/delta views ("up from 10 yesterday, down from 200 last week"). A live dashboard without history only shows a snapshot — history makes it tell a story.

**Not for performance**: Query APIs are fast enough. This is purely a history feature.

**When to build**: After one panel works end-to-end with live data. Don't design the storage schema until the data shape is known.

---

## Next.js App Router with server components

**Decision**: Server components fetch data directly — no separate API layer.

**Why**: Data fetching colocated with the component that renders it fits the config-driven panel architecture. Each panel is an isolated server component that reads its own config slice and fetches its own data. No global state complexity.

**Tradeoff**: Next.js carries opinions and weight beyond what a personal local tool needs. Accepted because familiarity reduces friction, and the server component model is genuinely well-suited to this pattern.

---

## Local-only to start

**Decision**: No deployment, no auth, no hosting concerns for now.

**Why**: Single user (the owner), running on personal or work laptop. `op run` for secrets works perfectly in this context. Deployment is a future concern once the tool proves its value.
