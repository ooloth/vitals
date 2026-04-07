# Scan Cadence

Scheduled scans are how agency manages entropy in the projects it observes.
Entropy is the natural tendency of codebases to drift — toward more dead code,
more outdated dependencies, more unhandled error paths, more undocumented
decisions. Left unchecked, drift compounds.

A scan that runs nightly catches drift early, when it is cheap to address. A
scan that runs weekly catches it later, when it has had time to spread. A scan
that runs only on demand catches it only when someone remembers to look.

The cadence decision belongs to cron, launchd, or GitHub Actions — not to
agency's config. Keeping the schedule external keeps it adjustable without
touching agency itself.

---

## Recommended cadences

| Signal type            | Cadence      | Rationale                                        |
| ---------------------- | ------------ | ------------------------------------------------ |
| Logs / error rates     | Nightly      | Spikes are time-sensitive; stale data is noise   |
| Codebase quality       | Weekly       | Code changes slowly; daily runs produce noise    |
| Dependencies           | Weekly       | CVEs matter; daily creates alert fatigue         |
| Deployments / PRs      | Daily        | Staleness compounds quickly                      |
| Harness retrospective  | Weekly       | Cross-run patterns need accumulation; weekly gives enough data without losing signal to noise |
| Issue grooming         | Before fixes | Ensures every issue the fix loop receives is still valid against the current codebase          |

These are starting points. A high-traffic service with volatile logs may need
more frequent scans; a stable library that changes rarely may need fewer.

---

## Backpressure

Cadence and fix loop throughput must be matched. A nightly scan that opens 10
issues will outpace a fix loop that closes 2 per day. The backpressure cap in
`projects.json` prevents the issue queue from growing unboundedly — when open
`ready-for-agent` issues exceed the cap, the scan skips rather than piling on.

See also: the backpressure check in the scan coordinator.
