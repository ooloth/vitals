# vitals

Autonomous agent loops that scan projects for problems and fix them.

Two loops. One interface between them.

```
scan → GitHub issues → fix
```

**Scan** runs read-only: queries logs, reads codebases, surfaces anything worth
acting on, and posts well-formed GitHub issues. **Fix** runs write: picks up
open issues, implements solutions in fresh agent subprocesses, and opens PRs
after a review pass. GitHub issues are the handoff — scan and fix are
deliberately decoupled.

---

## Setup

```bash
uv sync --all-extras
```

## Running

```bash
# scan a project for codebase improvements (dry run — prints without posting)
uv run python run.py scan vitals --type codebase --dry-run

# scan and post issues
uv run python run.py scan vitals --type codebase

# fix a specific issue in a specific project
uv run python run.py fix --issue 3 --project vitals

# fix the next open issue labelled 'agent'
uv run python run.py fix

# with secrets from 1Password
op run --env-file=secrets.env -- uv run python run.py scan pilots --type logs
```

---

## How it works

Each loop is a short Python function that sequences `claude -p` subprocesses.
Every subprocess is a fresh context window. The coordinator passes structured
JSON between steps via a temp file — the agent writes output to a path
provided in the prompt, the coordinator reads it back.

**Scan loop:**

```
find problems → triage/cluster → draft issues → review until ready → post
```

**Fix loop:**

```
implement → review → revise with feedback → open PR
```

Both loops escalate after a configurable number of rounds rather than running
forever. The coordinator makes two decisions per step: did the output pass
validation, and what runs next. All intelligence lives in the prompts.

---

## Structure

```
run.py                     entry point: scan | fix
loops/
  scan.py                  scan loop coordinator (~70 lines)
  fix.py                   fix loop coordinator (~60 lines)
prompts/
  scans/
    codebase.md            scan type: code quality improvements
    logs.md                scan type: error and anomaly detection
  triage.md                deduplicate and cluster raw findings
  draft-issues.md          write GitHub issue drafts from clusters
  review-issues.md         review issues before posting
  implement.md             implement a fix from an issue
  review.md                review an implementation before PR
projects/
  projects.toml            registry: which projects, which scans, data sources
  <id>/
    context.md             per-project context: what's normal, what to ignore
docs/                      architecture, decisions, philosophy, roadmap
secrets.env.example        template for 1Password secret references
```

---

## Extending

**Add a scan type** — create `prompts/scans/<type>.md` following the output
format contract (see any existing scan prompt). Register it in `projects.toml`
under the relevant project's `scans` array.

**Add a project** — add a `[[projects]]` entry to `projects/projects.toml`
with an `id`, `name`, and `scans` list. Add `projects/<id>/context.md` to
tell agents what's normal for that project.

**Add a step to a loop** — add one `agent()` call in the relevant coordinator
function. Pass the previous step's output as context. The new prompt must write
JSON to the output file.

**Add a fix strategy** — add prompts and a coordinator function in `loops/fix.py`.
The fix loop is young; the current implement→review pattern is the starting
point, not the ceiling.

---

## What not to do

- Don't add business logic to the coordinator. If you find yourself writing
  conditional logic that interprets the *content* of agent output (beyond
  checking `ready` or `approved`), it belongs in a prompt.

- Don't add a web UI, API layer, or database. This is a local tool that runs
  from the terminal and posts to GitHub. Adding a server changes the entire
  operational model.

- Don't add abstractions for one-off operations. Three similar lines of code
  is better than a premature abstraction. The coordinator is meant to be read
  and understood in five minutes.

- Don't have agents output to stdout and parse the text. Agents write JSON to
  a file. The coordinator reads the file. This is the handoff contract.

---

## Prerequisites

- `uv` (`brew install uv`) — manages the Python environment and dependencies
- `claude` CLI (`npm install -g @anthropic-ai/claude-code`)
- `gh` CLI (GitHub issues and PRs)
- `op` CLI (1Password, for secrets injection)
- A GitHub repo for each project you want the fix loop to operate on
