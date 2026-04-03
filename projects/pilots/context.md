# Pilots — project context

What's normal, what to ignore, and what matters.

## What this project is

A personal media server for tracking and watching TV pilots.

## Normal baseline

- A few hundred log lines per day during active use
- Auth errors from unauthenticated probes are expected and ignorable
- Background sync jobs run nightly; slow queries there are normal

## What to flag

- Any error spike above ~10/hour during off-hours
- Auth failures from known internal IPs (would indicate a real issue)
- Database connection errors (pool exhaustion has happened before)

## What to ignore

- `probe: unknown route` — bots, not users
- `favicon.ico 404` — not a real error
