# Coordinator restores original branch on exit

**Decision**: `run_fix` captures the current branch before doing any work and
restores it in a `finally` block, whether the run succeeds, fails, or
escalates.

**Why**: `prepare_branch` calls `git checkout <base>` and
`git checkout -b fix/issue-<N>` as side effects. Without cleanup, every fix
run leaves the repo on the fix branch. The user's environment is modified
without their knowledge. The `finally` block makes the coordinator's git
footprint zero-net: you get back to where you started regardless of what
happened.

**Implication**: Never remove the `finally` block from `run_fix` thinking it
is unnecessary. It is the only thing that prevents the repo from being left on
a fix branch after an unattended run.
