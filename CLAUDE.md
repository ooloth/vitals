# CLAUDE.md

## Commands

- Run checks: `uv run --frozen prek run --all-files`
- Run tests: `uv run --frozen pytest`

```bash
# Scan a project (dry run — prints without posting issues)
uv run --frozen python run.py scan <project-id> --type <scan-type> --dry-run

# Scan a project and post github issues
uv run --frozen python run.py scan <project-id> --type <scan-type>

# Fix a GitHub issue
uv run --frozen python run.py fix --issue <number>

# With secrets from 1Password
op run --env-file=secrets.env -- uv run --frozen python run.py scan <project-id>
```

## References

| What                                            | Where                                                                                          |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Philosophy and goals                            | [docs/philosophy.md](docs/philosophy.md)                                                       |
| Invariants to uphold                            | [docs/rules.md](docs/rules.md)                                                                 |
| Design decisions                                | [docs/decisions/](docs/decisions/)                                                             |
| Auth strategies by provider                     | [docs/architecture/auth.md](docs/architecture/auth.md)                                         |
| Scan cadence and entropy management             | [docs/architecture/scan-cadence.md](docs/architecture/scan-cadence.md)                         |
| Harness self-improvement                        | [docs/architecture/harness-self-improvement.md](docs/architecture/harness-self-improvement.md) |
| Conventions                                     | [docs/conventions/](docs/conventions/)                                                         |
| How to add projects, scan types, debug failures | [docs/playbooks/](docs/playbooks/)                                                             |
| Registered projects and data sources            | [projects/projects.json](projects/projects.json)                                               |
| Open issues to fix                              | `gh issue list`                                                                                |
