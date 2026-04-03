# CLAUDE.md

## Commands

- Run checks: `uv run prek run --all-files`
- Run tests: `uv run pytest`

```bash
# Scan a project (dry run — prints without posting issues)
uv run run.py scan <project-id> --type <scan-type> --dry-run

# Scan a project and post github issues
uv run run.py scan <project-id> --type <scan-type>

# Fix a GitHub issue
uv run run.py fix --issue <number>

# With secrets from 1Password
op run --env-file=secrets.env -- python3 run.py scan <project-id>
```

## References

| What                                            | Where                       |
| ----------------------------------------------- | --------------------------- |
| Philosophy and goals                            | [docs/philosophy.md](docs/philosophy.md)               |
| Invariants to uphold                            | [docs/rules.md](docs/rules.md)                         |
| Design decisions                                | [docs/decisions/](docs/decisions/)                     |
| Roadmap                                         | [docs/roadmap.md](docs/roadmap.md)                     |
| Auth strategies by provider                     | [docs/architecture/auth.md](docs/architecture/auth.md) |
| Scan cadence and entropy management             | [docs/architecture/scan-cadence.md](docs/architecture/scan-cadence.md) |
| Conventions                                     | [docs/conventions/](docs/conventions/)                 |
| How to add projects, scan types, debug failures | [docs/playbooks/](docs/playbooks/)                     |
| Discoveries from running the loops              | [docs/learnings/](docs/learnings/)                     |
| Registered projects and data sources            | [projects/projects.json](projects/projects.json)       |
| Open issues to fix                              | `gh issue list`                                        |
