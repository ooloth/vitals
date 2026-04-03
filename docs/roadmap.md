# Roadmap

## Phase 1: Validated coordinator (current)

- [x] Thin Python coordinator with fresh-context-per-step via `claude -p`
- [x] Scan loop: find → triage → draft issues → review until ready → post
- [x] Fix loop: implement → review → revise with feedback → open PR
- [x] Dry-run mode for scan
- [x] End-to-end scan validated (codebase scan of agency itself)

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
- [x] Harden reviewer: sees actual git diff (not just implementation summary),
      runs existing tests, reports results explicitly
- [x] Coordinator owns branch lifecycle: dirty-tree check, pull latest,
      create branch, deterministic commit after implement, restore original
      branch on exit, push before PR
- [x] Per-project install/checks/tests commands; coordinator runs them to
      verify clean state before starting work
- [ ] Issue locking: claim an issue with an `agent-fix-in-progress` label
      before starting work; release it on exit (including on error) so two
      concurrent runs can't collide on the same issue
- [ ] No-changes diagnostics: when the implement agent produces no diff,
      post its raw first response as a comment on the issue and remove the
      `ready-to-fix` label so a human can see why it stalled instead of
      silently retrying the round
- [ ] Review trail as PR comment: after opening the PR, append a collapsible
      summary of every implement/review iteration (iteration count,
      approved/rejected breakdown, last iteration open) so reviewers can
      understand the run without watching it live
- [ ] Use `--force-with-lease` on `git push` instead of plain `-u origin
      branch` so amended branches can be re-pushed safely without
      overwriting unexpected remote state
- [ ] Staleness scan: new scan type that batch reviews open agent-labelled
      issues against the current codebase, comments and closes stale ones
      before the fix loop picks them up (`--type staleness`)
- [ ] Local branch cleanup after PR is merged (roadmap only — manual for now)
- [ ] Learning step: post-loop reflection prompt that examines the run and
      outputs suggested improvements to agency's own prompts/coordinator as
      GitHub issues; open question: how to capture the full run transcript
      for the reflection agent to read (tee stdout to a log file?)

### Project config

- [x] Structured scan config in `projects.json`: required `normal`, `flag`,
      and `ignore` arrays per scan block calibrate the agent to each project's
      signal and noise; `projects.schema.json` enforces required fields
- [x] Migrated from `projects.toml` + per-project `context.md` files
- [ ] Replace hand-authored `projects.schema.json` with Pydantic models:
      define `Project`, `LogsScan`, `CodebaseScan` models; parse through them
      in `load_project()` for typed access and load-time validation; generate
      `projects.schema.json` from `model_json_schema()` so editors keep their
      schema file but there is only one source of truth; delete the
      hand-authored schema
- [ ] Effort/model per role: pass `--effort` (and optionally a model override)
      to each claude invocation independently so the reviewer can run at high
      effort without paying for it on the implement step; configurable in
      `projects.json` per project

## Phase 2: Schedulable scans

- [ ] launchd job for nightly scan runs (cadence stays in cron, not in config)
- [ ] Log scan prompt (Axiom) validated against real data
- [ ] Scan multiple projects and scan types in one invocation

## Phase 3: Trusted fix loop

- [ ] Fix loop validated end-to-end on real issues
- [ ] Escalation path: issues the fix loop can't resolve get flagged for human
      review (exit non-zero, add label, post comment explaining why)
- [ ] Fix loop picks up issues automatically (no --issue flag needed)
- [ ] Agentic review post: after a fix loop run, post a human-readable summary
      of what was attempted, what passed review, what was escalated

## Phase 4: Scan library

The loops are fixed infrastructure. The scan library is what grows. Each new
scan type is a prompt file + schema-validated config block — no coordinator
changes required.

- [ ] `staleness` — review open issues against current codebase before fix loop runs
- [ ] `dependencies` — flag outdated or vulnerable packages
- [ ] `costs` — flag unexpected spend spikes (cloud, API usage)
- [ ] `deployments` — flag failed or stalled deploys
- [ ] `open-prs` — flag PRs that have gone stale or need attention
- [ ] Per-project backpressure: cap by scan type/label so a noisy daily scan
      doesn't starve weekly ones

## Phase 5: Scheduling fix loops

- [ ] Nightly or triggered fix runs (scan finds → fix loop acts)
- [ ] Human-in-the-loop escalation for low-confidence fixes

## Future: Spec-based fix (no issue required)

Run the fix loop against a local spec file or inline prompt without
needing a GitHub issue — `python run.py fix -f spec.md` or
`fix -p "description"`. Useful for one-off tasks and for developing
a spec before turning it into a tracked issue. Naturally pairs with
a plan step that produces the spec.

## Future: Plan (develop a spec interactively)

An interactive session where an agent explores the codebase, asks
clarifying questions, presents options, and converges on an approach —
outputting a structured spec file ready for the fix loop or Ralph.
Out of scope until spec-based fix is in place.

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
