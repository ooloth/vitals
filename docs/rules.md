# Rules

Invariants that must hold across the entire system. When something feels
wrong or a change feels awkward, check it against these first.

---

## Coordinator rules

**The coordinator never interprets content.**
It checks structure — `ready`, `approved`, `findings` — but never makes
decisions based on what the content says. If you find yourself writing
`if "database" in cluster["title"]`, that logic belongs in a prompt.

**Each agent step runs in a fresh subprocess.**
Never reuse a running agent session across steps. The whole point of
`claude -p` is a clean context window for each step. Passing prior context
explicitly is intentional; inheriting it implicitly is not.

**Agents write output to a file. The coordinator reads the file.**
Agents do not return results via stdout. The coordinator passes a temp file
path in the prompt; the agent writes valid JSON there. This is the handoff
contract. Do not parse agent response text.

**JSON is the handoff format between steps.**
Every prompt defines an output schema. The coordinator passes the previous
step's JSON output as context to the next step. Steps are not coupled to each
other — only to the JSON contract.

**Loops escalate, not fail silently.**
When a loop does not converge within `max_rounds`, it posts a failure comment
on the issue, labels it `agent-fix-stalled`, and exits with a non-zero status.
Silent completion of a broken loop is worse than a loud failure.

---

## Issue quality rules

These apply to every GitHub issue posted by the scan loop.

**Rule 1 — Reference by snippet, never by location.**
Issues must include the problematic code verbatim so the implementer can grep
for it. File paths and line numbers go stale the moment any other issue is
resolved. The code snippet is stable.

**Rule 2 — Acceptance criteria describe observable outcomes, not
implementation choices.**
Every criterion must follow "run X, observe Y." It must be verifiable by
running something and observing the result — not by reading the code. Never
prescribe how to fix something; only describe what the fixed state looks like
from the outside.

These rules are enforced by the `review-issues.md` prompt, which rejects
drafts that violate either rule before they are posted.

---

## Prompt rules

**Prompts define the output schema explicitly.**
Every prompt includes a JSON example showing the exact shape the coordinator
expects. If the schema changes, update both the prompt and the coordinator.

**Prompts are the place for judgment, not Python.**
What counts as a "real" finding, how many issues to open, what severity means,
what "approved" requires — all of this belongs in the prompts. The coordinator
only checks whether the required keys are present and truthy.

---

## Project registry rules

**Use `~` not absolute paths.**
`path` values in `projects.json` must use `~/...` notation so the config is
machine-agnostic. The coordinator expands `~` at runtime.

**Secrets stay out of config.**
`projects.json` holds non-secret config only. Tokens and keys are referenced
as env var names (e.g. `"${AXIOM_TOKEN}"`), injected at runtime via
`op run --env-file=secrets.env`.

**Every scan block must provide `normal`, `flag`, and `ignore`.**
These are required fields, not optional documentation. They are what the scan
agent uses to distinguish signal from noise for that specific project. A scan
block without them will produce low-quality findings regardless of how good
the prompt is. The schema in `projects.schema.json` enforces their presence —
do not relax this constraint.
