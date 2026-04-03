# Learnings

Discoveries made while running the loops — things that surprised us, things
that didn't work the way we expected, and adjustments made as a result.

---

## Parsing agent output via stdout is fragile

**What happened**: The first implementation of `agent()` used
`--output-format json` and parsed `outer["result"]` from the Claude CLI
envelope. When issue bodies contained embedded code blocks, the markdown
fence-stripping logic found an inner ` ``` ` instead of the outer closing
fence and produced a `JSONDecodeError`.

**What we learned**: Agent text output is not a reliable JSON transport once
prompts produce content with embedded markdown. The output format is not under
our control.

**What changed**: Agents now write JSON to a temp file path provided in the
prompt. The coordinator reads the file. No text parsing required.

---

## `claude -p` has full tool access in non-interactive mode

**What we assumed**: Print mode might be read-only or have reduced tool
access.

**What we found**: `claude -p` has the same tool access as interactive mode —
read files, write files, run bash commands. The Write tool works exactly as
expected when the agent is asked to write JSON to a file path.

---

## Print order requires explicit flushing

**What happened**: Coordinator progress lines (`[scan] finding problems...`)
appeared *after* the subprocess output they were meant to precede, because
Python buffers stdout while subprocess streams directly to the terminal.

**What changed**: All coordinator `print()` calls that precede a subprocess
now use `flush=True`.

---

## `claude -p` requires `--allowedTools` for write operations

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

---

## `git stash` across branches causes merge conflicts

**What happened**: We stashed uncommitted changes on the `fix/issue-1` branch,
switched to `main`, and ran `git stash pop`. Git merged the stash changes with
`main`'s diverged state and produced a conflict in `loops/scan.py`.

**What we learned**: `git stash pop` is a merge. If the stashed changes
overlap with commits on the target branch, you get a conflict with no clean
way back. This is easy to trigger when bouncing between `main` and fix branches
during active development.

**What changed**: Nothing structural — this is a human workflow trap. When
working across branches, always commit or discard changes before switching.
Never stash across a branch boundary.

---

## Scan loop convergence on first review round is common

**What we found**: The `review-issues.md` prompt with the two rules (snippet
references, observable-outcome AC) typically passes on the first round. The
feedback loop is insurance, not the common path.

**Implication**: Five rounds is a generous default. If a scan consistently
needs more than two rounds, the drafting prompt needs improvement, not more
rounds.
