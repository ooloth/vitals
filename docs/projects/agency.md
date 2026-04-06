# Project context: Agency

## Doc categories and their purpose

| Location             | Purpose                                                                          |
| -------------------- | -------------------------------------------------------------------------------- |
| `README.md`          | Public-facing overview: what agency is, how to configure and run it              |
| `CLAUDE.md`          | In-session context for Claude Code: commands and reference table                 |
| `docs/philosophy.md` | Design principles and reasoning behind key choices                               |
| `docs/rules.md`      | Invariants the codebase must uphold                                              |
| `docs/architecture/` | How specific subsystems work; may describe design intent ahead of implementation |
| `docs/conventions/`  | Code and doc style rules                                                         |
| `docs/decisions/`    | ADR-style records of why key choices were made                                   |
| `docs/playbooks/`    | Step-by-step guides for common operator tasks                                    |
| `docs/projects/`     | Per-project context injected into scan and fix prompts (this file)               |
| `prompts/`           | Agent prompts — source of truth for what each step is expected to produce        |

## Two categories of documentation

Agency has two distinct categories of documentation:

1. **Docs about the harness itself** (`docs/`, `README.md`, `CLAUDE.md`,
   `prompts/`) — describe how agency works, what its loops do, how to run
   and configure it
2. **Docs about external projects** (`docs/projects/<id>.md`,
   `projects/projects.json`) — context files describing the projects agency
   monitors; these describe those external projects, not agency's own behaviour

Category 2 files should be evaluated against the external projects they
describe, not against agency's own codebase.
