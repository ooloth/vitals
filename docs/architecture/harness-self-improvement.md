# Harness Self-Improvement

Agency improves itself by observing its own runs. Every run captures agent
reflections and raw transcripts into `.logs/`. A periodic retrospective scan
reads that accumulated data across recent runs, detects cross-run patterns,
and produces GitHub issues through the standard scan pipeline — with the same
draft→review quality gate that governs all other issues.

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
from the agent's perspective, not what should change. The retrospective scan
draws conclusions.

### 2. Transcript capture (mechanical, per-run)

During each step, the coordinator tees every raw stream-json line from the
Claude subprocess into `{step}-transcript.jsonl` in the run directory.
No agent call — this is purely mechanical I/O.

### 3. `.logs/` directory

One directory per run, written by the Python loop script:

```
.logs/
  {YYYY-MM-DD}-{HH-MM}-{project}-{scan-type|fix-N}/
    metadata.json               ← run type, project, step durations, convergence, exit code
    reflections.json            ← all reflections collected from this run's steps
    find.json                   ← step output (scan runs)
    find-transcript.jsonl       ← raw Claude stream-json (scan runs)
    triage.json                 ← step output (scan runs)
    triage-transcript.jsonl
    draft.json                  ← step output (scan runs)
    draft-transcript.jsonl
    review-N.json               ← step output (scan runs, per round)
    review-N-transcript.jsonl
    implement-N.json            ← step output (fix runs, per round)
    implement-N-transcript.jsonl
    review-N.json               ← step output (fix runs, per round)
    review-N-transcript.jsonl
```

Gitignored. Runtime output, not source. The retrospective scan reads recent
entries from `.logs/` when looking for cross-run patterns.

### 4. Periodic retrospective scan (`agency/retrospective`)

A standard scan type — uses the same find→triage→draft→review pipeline as
any other scan. The find agent reads recent `.logs/` run directories using
Read, Glob, and Grep, then outputs findings in the standard format.

Running through the full pipeline means:

- Draft quality is checked by the review agent before posting
- No findings bypass the review gate
- Informational observations that don't meet the issue bar are discarded
  cleanly, not silently lost

**Recommended cadence:** after every N runs, or daily if runs accumulate.
See `docs/architecture/scan-cadence.md`.

**What the find agent looks for:**

- Non-convergence patterns: runs where `converged: false` appearing repeatedly
- Excessive rounds: step round counts well above normal
- Repeated reflections: the same agent observation across multiple steps or runs
- Review rejections for the same rule violation across multiple drafts
- Wasted work: steps that repeat without progress

**Reasoning standard:** the find agent is expected to reason structurally.
When it sees a failure mode, the right answer is almost never "remind the
agent to do X." It is usually:

- This should be done deterministically in Python before/after the agent step
- The prompt was missing context the agent needed
- The output schema allowed ambiguity the agent resolved incorrectly
- The loop structure created a situation the agent couldn't handle

### 5. GitHub issues (reflection issues)

One issue per distinct actionable pattern, produced by the standard scan
pipeline and therefore subject to the same review gate. They follow the same
three-section format as all scan-generated issues:

- **Problem** — what was observed, with evidence from the run data
- **Definition of done** — what the fixed state looks like from the outside
- **Out of scope** — what this issue does not ask for

**Labels:**

| Label               | Meaning                                          |
| ------------------- | ------------------------------------------------ |
| `autonomous`        | All agent-created issues                         |
| `needs-human-review`| Awaiting human review before any action          |
| `scan:retrospective` | Retrospective-generated (harness improvement)   |

Retrospective issues do **not** carry the `ready-for-agent` label when opened.
The fix loop will not pick them up until a human reviews the issue and adds
`ready-for-agent`.

---

## End-to-end flow

```
During run:
  each agent step → reflections[] in JSON output
  Python loop     → writes step JSON + transcript to .logs/{run}/
  Python loop     → writes metadata.json + reflections.json on exit

Periodically (human or scheduler):
  run: uv run --frozen run.py scan agency --type agency/retrospective

Retrospective scan (standard pipeline):
  find agent  → reads recent .logs/ entries, outputs findings[]
  triage      → clusters findings
  draft       → writes GitHub issue bodies
  review      → quality gate (rejects if issue violates rules)
  post        → opens issues with autonomous + needs-human-review + scan:retrospective labels

Human reviews issue:
  → closes if wrong/irrelevant
  → edits if partly right
  → adds ready-for-agent label when satisfied

Fix loop picks up issue:
  → implements harness change (prompt edit, loop change, etc.)
  → opens PR as normal

Human reviews and merges PR:
  → improvement is now in the prompt or loop code
  → reflection issue is closed
```

---

## Future: Axiom ingestion for run telemetry

The current design reads `.logs/` with Glob/Read/Grep. This works at current
scale but has structural limits:

- No cross-machine visibility — each machine has its own `.logs/`
- Agent context limits — reading many transcript files eats context fast
- No correlation with external signals (GitHub activity, deploy events)
- No retention policy — old runs accumulate indefinitely

**Key insight:** The stream-json transcript lines are already structured events.
Each line is valid JSON with a `type` field and content blocks containing tool
calls, text, and results. They are not blobs. This means _all_ run data
(metadata, reflections, and transcripts) can be ingested into Axiom as discrete
queryable events, tagged with run/step/project metadata.

**Proposed architecture:**

- **Terminal display**: unchanged — `_print_event()` parses and shows
  human-readable output during the run
- **Axiom ingestion**: each stream-json line is sent to Axiom as a structured
  event alongside the terminal display (same raw line, extra ingestion call)
- **Retrospective scan**: queries Axiom APL instead of reading files
  (e.g. `where type == "assistant" and run.converged == false | summarize count() by step`)
- **`.logs/`**: becomes an optional local cache, not the source of truth

This approach requires adding an Axiom dataset and ingestion call in `agent()`,
plus an APL-based find prompt for the retrospective scan type.

**When to tackle:** when file-based reading becomes a limitation — multi-machine
runs, too many runs to fit in agent context, or need for cross-signal
correlation. The existing logs/error-spikes scan already shows the APL query
pattern.

---

## What makes a good reflection issue

The retrospective scan agent should meet this bar:

- **Specific** — names the step, the round, the duration, the agent's own words
- **Causal** — explains why the failure happened, not just that it happened
- **Principled** — proposes a remedy consistent with the project's philosophy
  (determinism over agent judgment, thin coordinator, intelligence in prompts)
- **Structural** — prefers eliminating a failure mode over working around it
- **Falsifiable** — the definition of done is observable and verifiable

Issues that say "remind the agent to do X" are not good issues. The right
question is always: "should X be done deterministically in Python instead?"
