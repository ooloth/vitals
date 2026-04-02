# Roadmap

Rough sequence of work. Each item is a thin vertical slice — one panel, one source, end-to-end.

---

## Phase 1: Foundation (one panel, hardcoded)

- [ ] Scaffold Next.js app with App Router
- [ ] Define `vitals.config.toml` schema (TOML parsing via `smol-toml` or similar)
- [ ] Sidebar navigation driven by config (projects + panel types)
- [ ] One project, one panel (`errors`), hardcoded mock data
- [ ] Basic layout: sidebar + main content area

## Phase 2: Live data (one source)

- [ ] Pick one source (GCP Logging or Grafana Loki) for the errors panel
- [ ] Implement fetcher for that source
- [ ] Wire config params → fetcher → component
- [ ] `op run` secrets setup + `secrets.env` (gitignored)
- [ ] Verify end-to-end with real data

## Phase 3: History

- [ ] SQLite setup (`better-sqlite3`)
- [ ] Store each panel result with timestamp on page load
- [ ] Show delta vs previous snapshot (count up/down)

## Phase 4: Second source

- [ ] Add a second data source for the errors panel (proves discriminated union pattern works)
- [ ] Add a second project using the new source

## Phase 5: Second panel type

- [ ] Add `deployments` panel (or whichever proves most useful)
- [ ] Validate the panel abstraction generalizes cleanly

## Phase 6: Agentic investigation

- [ ] "Investigate this" button on a panel → agent queries logs with context, returns narrative summary
- [ ] Streaming response display

## Phase 7: Scheduling

- [ ] `launchd` job or cron that triggers a background refresh on a schedule
- [ ] Stale data indicator in UI

## Phase 8: UI-based onboarding (long-term)

- [ ] Config editor UI (reads/writes `vitals.config.toml`)
- [ ] Dropdowns populated by querying provider APIs
- [ ] Credentials management UI (writes to `secrets.env`)
