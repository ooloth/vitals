# GitHub issues as the single task board

**Decision**: GitHub issues are the sole task tracker for all work — scan
findings, retrospective improvements, manually planned enhancements, and
speculative ideas alike. Labels distinguish type and readiness. The fix loop
reads only `ready-for-agent` issues; all other labels are invisible to agents.

**Why**: The alternative — tracking planned work in a `docs/roadmap.md`
file and scan output in GitHub issues — created two parallel lists with no
clear rule about which work belonged where. Items drifted into both, neither
stayed current, and planning sessions required reconciling two sources. A
single tracker with label-based filtering is more maintainable and queryable.

GitHub issues also compose well with the rest of the system: the scan loop
posts to them, the fix loop reads from them, the retrospective scan posts to
them, and `gh issue list` gives any agent or human a filtered view in one
command.

**Label taxonomy:**

| Label              | Applied by   | Meaning                                        |
| ------------------ | ------------ | ---------------------------------------------- |
| `autonomous`       | scan loop    | Opened by an agent                             |
| `needs-human-review` | scan loop  | Awaiting human review before any action        |
| `scan:codebase`    | scan loop    | Output of a codebase scan                      |
| `scan:logs`        | scan loop    | Output of a logs scan                          |
| `scan:retrospective` | scan loop  | Output of a scan-loop retrospective            |
| `fix:retrospective`  | scan loop  | Output of a fix-loop retrospective             |
| `sev:*`            | scan loop    | Severity (critical / high / medium / low)      |
| `ready-for-agent`  | human        | Reviewed and ready for the fix loop            |
| `fix-in-progress`  | fix loop     | Claimed by a running fix loop instance         |
| `enhancement`      | human        | Manually planned improvement                   |
| `idea`             | human        | Speculative — no definition of done yet        |

**What agents read:**

The fix loop queries `--label ready-for-agent` to find its next issue. No other
label causes the fix loop to act. Labels like `enhancement` and `idea` are
purely for human organisation — agents ignore them. The scan loop queries
`--label autonomous` when checking for duplicate titles before posting.
The backpressure cap counts `--label ready-for-agent` issues — the depth of the
fix loop queue — not all autonomous issues.

**`docs/roadmap.md` is deleted.** All work — speculative ideas, planned
enhancements, and scan findings — lives in GitHub issues. The `idea` label
covers speculative items with no definition of done yet; `enhancement`
covers planned improvements. Architecture docs (`docs/architecture/`,
`docs/decisions/`) are the right home for design reasoning that doesn't fit
an issue.
