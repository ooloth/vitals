# Roadmap

## Phase 1: Validated coordinator (current)

- [x] Thin Python coordinator with fresh-context-per-step via `claude -p`
- [x] Scan loop: find → triage → draft issues → review until ready → post
- [x] Fix loop: implement → review → revise with feedback → open PR
- [x] Dry-run mode for scan
- [x] End-to-end scan validated (codebase scan of vitals itself)

### Prompt quality (from agency audit)

- [x] Rewrite `draft-issues.md` with three-section structure:
      Problem (description + inline snippet) / Definition of done (outside-in
      observable proof, not exhaustive) / Out of scope
- [x] Port adversarial review rubric into `review.md`: five-point ordered
      checklist (Approach → Correctness → Regressions → Edge Cases →
      Completeness); approach-first gate ("if approach is wrong, stop here");
      proportionality rule; structured LGTM/CONCERNS verdict with required
      "Required Changes" section; explicit anti-rubber-stamp instruction
- [x] Port fix prompt wording into `implement.md`: "minimal changes needed",
      "prefer simplest solution, avoid problems rather than handle them",
      "line numbers are hints only — locate by symbol name"

### Scan loop reliability

- [x] Add issue deduplication: before posting, check for existing open issues
      with matching title; start with title match, later grow to reading
      descriptions and posting as comment on duplicate
- [x] Add backpressure check: if open `agent`-labelled issues exceed a cap,
      skip the scan run rather than piling on more issues the fix loop hasn't
      cleared yet (lives inside scan coordinator, scheduled externally via launchd)

### Fix loop reliability

- [ ] Validate fix loop end-to-end on issues #1–4 (dogfood)
- [ ] Harden reviewer: sees actual git diff (not just implementation summary),
      runs existing tests, reports results explicitly
- [ ] Staleness scan: new scan type that batch reviews open agent-labelled
      issues against the current codebase, comments and closes stale ones
      before the fix loop picks them up (`--type staleness`)

## Phase 2: Schedulable scans

- [ ] launchd job for nightly scan runs
- [ ] Scan multiple projects and scan types in one run
- [ ] Per-project context docs for all monitored projects
- [ ] Log scan prompt (Axiom) validated against real data

## Phase 3: Trusted fix loop

- [ ] Fix loop validated end-to-end on real issues
- [ ] Escalation path: issues the fix loop can't resolve get flagged for human
      review (exit non-zero, add label, post comment explaining why)
- [ ] Fix loop picks up issues automatically (no --issue flag needed)
- [ ] Agentic review post: after a fix loop run, post a human-readable summary
      of what was attempted, what passed review, what was escalated

## Phase 4: Breadth

- [ ] Additional scan types: deployments, costs, open PRs, dependency drift
- [ ] Additional fix types: config changes, dependency updates
- [ ] Multiple projects registered and scanning cleanly

## Phase 5: Scheduling fix loops

- [ ] Nightly or triggered fix runs (scan finds → fix loop acts)
- [ ] Human-in-the-loop escalation for low-confidence fixes

## Future: Ralph loop (iterative refinement)

A third loop type for open-ended goals that originate with the user rather
than scan results. Distinct from fix (which works from a specific issue) and
scan (which is read-only).

- Each iteration runs in a fresh context window
- Agent outputs a scratchpad block (Status / Key decisions / Remaining work);
  coordinator extracts and injects into next iteration — no accumulated history
- Commits after each iteration for crash safety and audit trail
- Terminates on `##DONE##` signal or max rounds
- Entry point: `python run.py refine "goal" --max-rounds N`
- Useful for: improving a prompt until it consistently produces good output,
  refactoring a module, implementing a feature from an open-ended description
- Parked for now — autonomous scan+fix is the priority

## Future: Plan + interactive workflows

Human-initiated workflows where a goal is explored interactively before
autonomous work begins. Different trust model from scan+fix (system-initiated).
Out of scope for this project; may belong in a separate tool.
