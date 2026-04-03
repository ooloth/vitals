# agency

> [!CAUTION]
> **Agency is a research project. If your name is not Michael Uloth, do not use it.**
>
> This software may change or break without notice. No support or warranty is provided.
> Use at your own risk.

Autonomous agent loops that scan projects for problems and fix them.

Two loops. One interface between them.

```
scan → GitHub issues → fix
```

**Scan** runs read-only: queries logs, reads codebases, or checks whatever
you configure — surfaces anything worth acting on, and posts well-formed
GitHub issues. **Fix** runs write: picks up open issues, implements solutions
in fresh agent subprocesses, and opens PRs after a review pass. GitHub issues
are the handoff — scan and fix are deliberately decoupled.

The loops are fixed. What varies is the scan configuration. Adding a new scan
type is adding a prompt file and a scan block in `projects.json`. Each project
configures each scan type with its own calibration — what's normal, what to
flag, what to ignore — while the same loop machinery handles orchestration,
triage, issue drafting, review, and posting for every scan type and every
project.

---

## Setup

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Usage

```bash
# scan a project (dry run — prints issues without posting)
uv run python run.py scan agency --type codebase --dry-run

# scan and post issues
uv run python run.py scan agency --type codebase

# fix a specific issue in a specific project
uv run python run.py fix --issue 3 --project agency

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
  scan.py                  scan loop coordinator (~50 lines)
  fix.py                   fix loop coordinator (~85 lines)
  common/                  shared infrastructure (git, github, agent, projects)
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
  projects.json            registry: projects, scan configs, data sources
  projects.schema.json     JSON Schema — documents and enforces required fields
docs/                      architecture, decisions, philosophy, roadmap
secrets.env.example        template for 1Password secret references
```

---

## Scan configuration

Each project in `projects.json` declares one or more scan blocks. Each scan
block carries the context that calibrates the agent to that project:

```json
{
  "type": "logs",
  "source": "axiom",
  "dataset": "my-app",
  "token": "${AXIOM_TOKEN}",
  "normal": ["A few hundred log lines per day during active use"],
  "flag": ["Error spike above ~10/hour during off-hours"],
  "ignore": ["favicon.ico 404 — not a real error"]
}
```

`normal`, `flag`, and `ignore` are required on every scan block. They are
what the scan agent uses to distinguish signal from noise. The schema enforces
their presence — a scan block without them will fail validation.

Different scan types accept different additional fields (`source`, `dataset`,
`token` for logs; nothing extra for codebase). See `projects.schema.json` for
the full contract.

---

## Extending

**Add a scan type** — create `prompts/scans/<type>.md` following the output
format contract (see any existing scan prompt). Add a scan block with
`"type": "<type>"` to the relevant project in `projects.json`, including
`normal`, `flag`, and `ignore` arrays calibrated for that project.

**Add a project** — add an entry to `projects/projects.json` with `id`,
`name`, and `scans`. Each scan block requires `normal`, `flag`, and `ignore`.
See `projects.schema.json` for all available fields (`path`, `install`,
`checks`, `tests`).

**Add a step to a loop** — add one `agent()` call in the relevant coordinator
function. Pass the previous step's output as context. The new prompt must write
JSON to the output file.

**Add a fix strategy** — add prompts and a coordinator function in `loops/fix.py`.
The fix loop is young; the current implement→review pattern is the starting
point, not the ceiling.

---

## What not to do

- Don't add business logic to the coordinator. If you find yourself writing
  conditional logic that interprets the _content_ of agent output (beyond
  checking `ready` or `approved`), it belongs in a prompt.

- Don't add a web UI, API layer, or database. This is a local tool that runs
  from the terminal and posts to GitHub. Adding a server changes the entire
  operational model.

- Don't add abstractions for one-off operations. Three similar lines of code
  is better than a premature abstraction. The coordinator is meant to be read
  and understood in five minutes.

- Don't have agents output to stdout and parse the text. Agents write JSON to
  a file. The coordinator reads the file. This is the handoff contract.
