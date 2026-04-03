# Harness Self-Improvement

Agency improves itself by observing its own runs. Each agent reflects on its
own step. A retrospective agent synthesises those reflections after every run,
persists a run report, and opens GitHub issues for actionable findings. The
fix loop can then implement harness improvements the same way it implements
any other fix — from a well-formed issue, with a PR for human review.

The goal is to surface failure modes and inefficiencies automatically, reason
from first principles about how to eliminate them (not just paper over them),
and route the resulting proposals through the same human-in-the-loop review
that governs all other changes to the system.

---

## Components

### 1. Reflections in step outputs

Every agent prompt includes a `reflections` array in its output schema. Each
entry is a first-person observation about that step's own run:

- What context was missing or ambiguous
- What caused retries or hesitation
- What would have made the step faster or more accurate
- Anything surprising about the inputs it received

```json
{
  "findings": [...],
  "reflections": [
    "The project context didn't specify the log retention policy — I had to infer it",
    "Flag threshold of 10/hour was ambiguous: per endpoint or aggregate?"
  ]
}
```

Reflections are observations, not instructions. They describe what happened
from the agent's perspective, not what should change. The retrospective agent
draws conclusions.

### 2. Retrospective agent

Runs as a final step after every scan or fix run, called by the Python loop
script after all other steps complete (including on convergence failure — a
failed run often has the most useful signal).

**Inputs:**
- All `reflections` arrays collected from this run's step outputs
- Run metadata: step durations, rounds per step, convergence result, exit code
- The `.logs/` files from recent prior runs (for cross-run pattern detection)
- All currently open GitHub issues labelled `agent-reflection` (to avoid
  duplicates and to add evidence to existing patterns)
- The prompt files that were active during this run (to propose targeted edits)

**Outputs:**
- A run report, always — printed to stdout and saved as `report.md` in the
  run's log directory (see below)
- Per actionable finding: a GitHub issue, or a comment on an existing issue
  if the same pattern already has one open (see Issue format below)

**Run report content:**
- Summary of steps: rounds taken, convergence result, total duration
- All agent reflections, grouped by step
- Retrospective findings: patterns detected, proposed root causes, proposed
  remedies (reasoned from first principles — "do this deterministically in
  Python" not "remind the agent")
- If nothing to report: an explicit "No observations. No known patterns
  detected." — a clean run is also worth recording

**Reasoning standard:** the retrospective agent is not a logging agent. It is
expected to reason from the project's principles (determinism over agent
judgment, thin coordinator, intelligence in prompts) and propose solutions
that eliminate failure modes structurally, not rhetorically. The branch/commit
example: seeing that an implementer spent 30 minutes with a reviewer rejecting
for missing commits, the right proposal is "do branch creation and final commit
deterministically in Python before and after the implement step" — not "remind
the implementer to commit."

### 3. `.logs/` directory

One directory per run, written by the Python loop script:

```
.logs/
  {YYYY-MM-DD}-{HH-MM}-{project}-{scan-type|fix-N}/
    report.md           ← retrospective agent's run report
    find.json           ← step output (scan runs)
    triage.json         ← step output (scan runs)
    draft.json          ← step output (scan runs)
    review.json         ← step output (scan runs)
    implement.json      ← step output (fix runs, per round)
    review.json         ← step output (fix runs, per round)
    run.log             ← full stdout (deferred — see note)
```

Gitignored. Runtime output, not source. The retrospective agent reads recent
entries from `.logs/` when looking for cross-run patterns.

**run.log (deferred):** capturing full stdout requires tee-ing the Python
process's output stream. Deferred until the JSON step outputs plus run metadata
prove insufficient for retrospective analysis.

### 4. GitHub issues (reflection issues)

One issue per distinct actionable finding. Issues are opened (or commented on)
by the retrospective agent using `gh`. They follow the same three-section
format as scan-generated issues:

- **Problem** — what was observed, with evidence from the run (step, round
  count, duration, agent's own reflection text)
- **Definition of done** — what the fixed state looks like from the outside,
  observable and verifiable
- **Out of scope** — what this issue does not ask for

**Labels:**

| Label | Meaning |
| --- | --- |
| `agent-reflection` | All retrospective-generated issues |
| `reflection:scan` | Scan loop behaviour (prompt quality, clustering, calibration) |
| `reflection:fix` | Fix loop behaviour (implementation, review, branch/commit) |
| `reflection:{project-id}` | Project-specific signal calibration |

Reflection issues do **not** carry the `ready-to-fix` label when opened. The
fix loop will not pick them up until a human reviews the issue and adds
`ready-to-fix`. This gives you the opportunity to close, edit, or comment
before any automated action is taken.

**Duplicate handling:** before opening a new issue, the retrospective agent
searches open `agent-reflection` issues for the same pattern. If found, it
comments on the existing issue with the new evidence rather than opening a
duplicate. A growing comment thread is a visible signal of priority.

### 5. `docs/learnings/` files

Durable record of *resolved* improvements. Written when the fix loop closes a
reflection issue by opening a PR — not during or after the run that surfaced
the observation. These files are not injected into prompts; the knowledge is
already in the updated prompt or loop code. They serve as a human-readable
history of how the harness has evolved.

**Files:**

| File | Contains |
| --- | --- |
| `docs/learnings/scan.md` | Resolved scan loop improvements |
| `docs/learnings/fix.md` | Resolved fix loop improvements |
| `docs/learnings/{project-id}.md` | Resolved project calibration improvements |

**Format:**

```
- YYYY-MM-DD [reflection:scan]: one or two lines describing what was observed
  and what the fix was. Closes #{issue-number}.
```

Append only. The history of past mistakes is useful.

---

## End-to-end flow

```
During run:
  each agent step → reflections[] in JSON output
  Python loop     → writes step JSON to .logs/{run}/

After run:
  Python loop → calls retrospective agent with:
                  all reflections, run metadata,
                  recent .logs/ entries,
                  open agent-reflection issues,
                  active prompt files

Retrospective agent:
  → always prints run report to stdout
  → saves report.md to .logs/{run}/
  → per actionable finding:
      open issue exists? → comment with new evidence
      no open issue?     → open new issue (agent-reflection + reflection:* labels)
                            no ready-to-fix label yet

Human reviews issue:
  → closes if wrong/irrelevant
  → edits if partly right
  → adds ready-to-fix label when satisfied

Fix loop picks up issue:
  → implements harness change (prompt edit, loop change, etc.)
  → appends entry to docs/learnings/{scan|fix|project-id}.md
  → opens PR as normal

Human reviews and merges PR:
  → improvement is now in the prompt or loop code
  → reflection issue is closed
```

---

## What makes a good reflection issue

The retrospective agent should be prompted to meet this bar:

- **Specific** — names the step, the round, the duration, the agent's own words
- **Causal** — explains why the failure happened, not just that it happened
- **Principled** — proposes a remedy consistent with the project's philosophy
  (determinism over agent judgment, thin coordinator, intelligence in prompts)
- **Structural** — prefers eliminating a failure mode over working around it
- **Falsifiable** — the definition of done is observable and verifiable

Issues that say "remind the agent to do X" are not good issues. The right
question is always: "should X be done deterministically in Python instead?"
