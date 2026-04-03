# `claude -p` requires `--allowedTools` for write operations

**What happened**: The implement agent consistently made the right code changes
but left them uncommitted in the working tree. Each review round saw an empty
diff. The agent's notes explained it could not run `git commit` because "git
commands require user approval in this permission mode."

**What we learned**: `claude -p` runs with a default permission model that
prompts for approval before bash commands and file writes. In a non-interactive
subprocess there is no one to approve, so the operation silently never happens.

**What changed**: The `agent()` call for the implement step passes
`--allowedTools Bash Read Write Edit Glob Grep`, giving it the permissions it
needs without manual approval. The reviewer gets `Read Glob Grep` only — it
has no business writing anything.

**Implication**: Any new agent step that needs to write files or run commands
must explicitly declare its tools. Omitting `--allowedTools` does not mean
"all tools allowed" — it means "prompt for approval", which in `-p` mode
means the operation never runs.
