"""Agentic scan loop: find problems, triage, draft issues, review, and post."""

import json
import sys

from loops.common import agent, load_project, log, open_issue_titles, post_issues, scan_context

BACKPRESSURE_CAP = 10


def run_scan(
    project_id: str, scan_type: str = "logs", max_rounds: int = 5, *, dry_run: bool = False
) -> None:
    """Scan a project for problems and post issues, respecting the backpressure cap."""
    if not dry_run:
        open_count = len(open_issue_titles())
        if open_count >= BACKPRESSURE_CAP:
            log.info(
                "[scan] %s open issues pending fix — skipping scan (backpressure cap: %s)",
                open_count,
                BACKPRESSURE_CAP,
            )
            return

    project = load_project(project_id)
    scan = next((s for s in project["scans"] if s["type"] == scan_type), None)
    if scan is None:
        msg = f"Project '{project_id}' has no '{scan_type}' scan configured"
        raise ValueError(msg)
    context = scan_context(project, scan)

    log.info("[scan] %s/%s: finding problems...", project_id, scan_type)
    raw = agent(f"prompts/scan/sources/{scan_type}.md", context)

    if not raw.get("findings"):
        log.info("[scan] %s/%s: nothing to report", project_id, scan_type)
        return

    log.info("[scan] %s finding(s) — triaging...", len(raw["findings"]))
    clustered = agent("prompts/scan/triage.md", json.dumps(raw))

    if not clustered.get("clusters"):
        log.info("[scan] %s/%s: no actionable clusters after triage", project_id, scan_type)
        return

    log.info("[scan] %s cluster(s) — drafting issues...", len(clustered["clusters"]))
    drafted = agent("prompts/scan/draft-issues.md", json.dumps(clustered))

    for round_n in range(max_rounds):
        log.info("[scan] reviewing issues (round %s)...", round_n + 1)
        reviewed = agent("prompts/scan/review-issues.md", json.dumps(drafted))
        if reviewed["ready"]:
            post_issues(reviewed["issues"], dry_run=dry_run)
            action = "would post" if dry_run else "posted"
            log.info(
                "[scan] %s/%s: %s %s issue(s)",
                project_id,
                scan_type,
                action,
                len(reviewed["issues"]),
            )
            return
        log.info("[scan] round %s: needs revision — %s", round_n + 1, reviewed["feedback"])
        drafted = agent("prompts/scan/draft-issues.md", json.dumps(reviewed))

    log.error(
        "[escalate] %s/%s: issues did not converge after %s rounds",
        project_id,
        scan_type,
        max_rounds,
    )
    sys.exit(1)
