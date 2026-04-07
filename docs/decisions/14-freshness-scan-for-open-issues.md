# Groom loop for open issues

**Decision**: A dedicated groom loop re-validates all open autonomous issues
against the current codebase. Issues whose problems have been resolved by
other changes are closed. Issues that are partially stale are edited to
reflect the current state. The fix loop is not involved.

**Why**: Code changes between issue creation and fix execution. When an issue
describes a problem that has since been resolved (or partially resolved),
the fix loop wastes a run discovering this — or worse, writes redundant code.
The reviewer then independently re-verifies the same staleness claims.

Issue accuracy is a maintenance concern. The scan loop creates issues; the
groom loop maintains them. The fix loop's contract is: every symptom in the
issue you receive is confirmed present in the current codebase.

**Scope**: All open issues with the `autonomous` label, regardless of other
labels (`ready-for-agent`, `needs-human-review`, `agent-fix-stalled`).
Manually-created issues are the human's responsibility.

**Approach**: The groom loop is a peer to scan and fix, invoked as its own
CLI command (`run.py groom <project>`). For each open autonomous issue, the
evaluate agent receives the issue and has read access to the target project's
codebase. It reads the issue holistically — not just code snippets — and
explores the codebase to judge whether each described problem is still
present, partially resolved, or fully resolved. No brittle snippet
extraction; the agent uses its judgment.

**Actions**:
- **All problems still present** → no change
- **Partially resolved** → edit the issue body to reflect current state
- **Fully resolved** → close the issue with a comment explaining what changed

**Cadence**: Scheduled to run before fix batches. Operationally coupled
(run groom, then run fixes) but not code-coupled — they remain independent
loops triggered by external scheduling.

**What this replaces**: Nothing. The fix loop currently has no staleness
detection. The implement prompt's guidance to "grep for snippets" is a
workaround, not a mechanism.
