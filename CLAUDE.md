# CLAUDE.md

## Running code

```bash
# scan a project (dry run — prints without posting issues)
python3 run.py scan <project-id> --type codebase|logs --dry-run

# scan and post issues
python3 run.py scan <project-id> --type codebase|logs

# fix an issue
python3 run.py fix --issue <number>

# with secrets from 1Password
op run --env-file=secrets.env -- python3 run.py scan <project-id>
```

## References

| What | Where |
|---|---|
| Philosophy and goals | `docs/philosophy.md` |
| Invariants to uphold | `docs/rules.md` |
| Design decisions | `docs/decisions.md` |
| Roadmap | `docs/roadmap.md` |
| Auth strategies by provider | `docs/architecture/auth.md` |
| How to add projects, scan types, debug failures | `docs/playbooks/README.md` |
| Discoveries from running the loops | `docs/learnings/README.md` |
| Registered projects and data sources | `projects/projects.toml` |
| Open issues to fix | `gh issue list` |
