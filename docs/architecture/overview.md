# Architecture

## What Vitals Is

A personal observability dashboard for one user (the owner). Aggregates answers to proactively useful questions across personal and work projects — errors, deployments, latency, etc. — in a single place.

Not a Sentry replacement. Not a generic monitoring platform. A curated, config-driven window into the systems you're responsible for, including an agentic "investigate this" capability for drilling into problems.

## Core Abstractions

### Project

A deployable system you want to monitor. Has a unique ID (used in URLs), a display name, and a list of panels.

### Panel

A question + a data source + a renderer. Each panel type (e.g. `errors`) has:
- One React component that renders the result
- One query function per supported data source
- A config block that declares which source to use and what params to pass

### Data Source

A provider of raw data (logs, metrics, deployment events, etc.). Each source has:
- A fetcher function that accepts typed params and returns structured data
- A TypeScript type for its params shape

## Config-Driven Architecture

Projects are onboarded via `vitals.config.toml` at the repo root. Each project declares which panels it supports and what params each panel needs.

The `source` field in each panel config is the discriminant — it determines which fetcher runs and which params shape is expected. This is modelled as a TypeScript discriminated union.

**Adding a new project**: add a block to `vitals.config.toml` — no code changes.
**Adding a new panel type**: add a component + query function(s) + config type.
**Adding a new data source for an existing panel**: add a fetcher + extend the discriminated union.

## Evolution Path

The config file is hand-authored to start. The long-term goal is a UI-based onboarding flow that generates the same config structure — dropdowns populated by querying provider APIs (e.g. list available GCP projects, Grafana datasources). The config schema is the form schema; the UI just writes it instead of the human.

## Tech Stack

- **Framework**: Next.js (App Router, server components)
- **Language**: TypeScript
- **Config format**: TOML (`vitals.config.toml`)
- **Persistence**: SQLite (for historical snapshots enabling trend/delta views)
- **Secrets**: 1Password CLI via `op run --env-file=secrets.env -- next dev`
- **Styling**: TBD

## Data Flow

```
vitals.config.toml
       ↓
Next.js server component (per panel, per page load)
       ↓
fetcher(source, params) → raw data
       ↓
SQLite (store snapshot with timestamp)
       ↓
render component → UI
```

## URL Structure

```
/                          → project list / home
/projects/[id]             → default panel for a project
/projects/[id]/[panelType] → specific panel
```

## What Vitals Is Not

- Not a real-time streaming dashboard (poll on page load is fine)
- Not multi-user (no auth, no accounts)
- Not a replacement for alerts (complements them — surfaces things that don't warrant alerts)
- Not a hosted service (runs locally only, for now)
