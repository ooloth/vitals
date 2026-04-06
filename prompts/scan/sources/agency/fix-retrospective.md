# Agency fix-loop retrospective scan

Review recent fix loop run data and surface patterns worth acting on.

## What you receive

A JSON object with the standard scan calibration:
- `normal` — patterns expected and not worth flagging
- `flag` — patterns that indicate a systemic problem worth a GitHub issue
- `ignore` — specific known issues to skip

## Your tools

Read, Glob, and Grep. These are the only tools available — do not attempt Bash. Each run
directory contains:

- `metadata.json` — run type, project, issue number, step durations, convergence
  result, total duration, exit code
- `reflections.json` — list of `{"step": name, "text": observation}` entries
  collected from each step's output
- `{step}-transcript.jsonl` — raw stream-json lines from the Claude subprocess;
  use this to see exactly what the agent did and said during that step
- `implement-N.json` — structured output from each implement round
- `review-N.json` — structured output from each review round

## How to approach this

1. **Review the pre-loaded run summaries.** The coordinator has already read
   `metadata.json` from each recent run directory and included the results as
   structured JSON in your context (see `## Recent run summaries` above). Filter
   to entries where `run_type == "fix"`. Use these to get an overview (issue
   number, converged?, round count, duration) without any extra Read calls. Each
   entry includes a `run_dir` path so you can navigate directly to step JSONs and
   transcripts when you need to go deeper.

2. **Look for patterns across runs** — not one-off anomalies, but the same
   failure mode appearing in multiple fix runs. Focus on:
   - Non-convergence: fix runs where `converged: false`
   - Excessive rounds: runs with unusually high implement+review round counts
   - No-diff outcomes: implement steps that produced no file changes
   - Repeated review rejections for the same rule violation across multiple issues
   - Repeated reflections: the same observation appearing in implement or review
     steps across multiple runs
   - Wasted work: review rejecting for reasons the prompt already addresses

3. **Read transcripts selectively.** Don't read every transcript. Use the
   metadata and step JSONs to identify which steps are worth deeper inspection,
   then read those transcripts to understand what actually happened.

4. **Reason structurally.** When you find a pattern, ask: why did this happen?
   The right remedy is almost never "remind the agent." It is usually:
   - This should be done deterministically in Python before/after the agent step
   - The implement prompt was missing context the agent needed
   - The review prompt's criteria were ambiguous or inconsistent
   - The loop structure created a situation the agent couldn't handle

## Output format

```json
{
  "findings": [
    {
      "title": "...",
      "body": "**Problem**\n...\n\n**Definition of done**\n...\n\n**Out of scope**\n..."
    }
  ],
  "reflections": []
}
```

`findings` follows the standard scan format — one entry per distinct actionable
pattern. Empty array if nothing warrants a GitHub issue.

`reflections` is for your own observations about this scan step (what was
missing, what would have helped). Usually empty.
