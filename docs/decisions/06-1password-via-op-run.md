# 1Password via `op run`

**Decision**: Secrets injected as env vars via
`op run --env-file=secrets.env -- python run.py <cmd>`.
Coordinator and agents read `os.environ` only — no SDK, no secrets on disk.

**Why**: Complete decoupling from 1Password at the code level. Swap secret
managers by changing `secrets.env`, not code. Secrets exist only in the
process environment for the lifetime of the run.
