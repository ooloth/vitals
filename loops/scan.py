import json
import sys

from loops.common import agent, load_project, post_issues, project_context, open_issue_titles

BACKPRESSURE_CAP = 10


def run_scan(project_id: str, scan_type: str = "logs", max_rounds: int = 5, dry_run: bool = False) -> None:
    if not dry_run:
        open_count = len(open_issue_titles())
        if open_count >= BACKPRESSURE_CAP:
            print(f"[scan] {open_count} open issues pending fix — skipping scan (backpressure cap: {BACKPRESSURE_CAP})")
            return
    context = project_context(project_id)

    print(f"[scan] {project_id}/{scan_type}: finding problems...", flush=True)
    raw = agent(f"prompts/scans/{scan_type}.md", context)

    if not raw.get("findings"):
        print(f"[scan] {project_id}/{scan_type}: nothing to report")
        return

    print(f"[scan] {len(raw['findings'])} finding(s) — triaging...", flush=True)
    clustered = agent("prompts/triage.md", json.dumps(raw))

    if not clustered.get("clusters"):
        print(f"[scan] {project_id}/{scan_type}: no actionable clusters after triage")
        return

    print(f"[scan] {len(clustered['clusters'])} cluster(s) — drafting issues...", flush=True)
    drafted = agent("prompts/draft-issues.md", json.dumps(clustered))

    for round_n in range(max_rounds):
        print(f"[scan] reviewing issues (round {round_n + 1})...", flush=True)
        reviewed = agent("prompts/review-issues.md", json.dumps(drafted))
        if reviewed["ready"]:
            post_issues(reviewed["issues"], dry_run=dry_run)
            print(f"[scan] {project_id}/{scan_type}: {'would post' if dry_run else 'posted'} {len(reviewed['issues'])} issue(s)")
            return
        print(f"[scan] round {round_n + 1}: needs revision — {reviewed['feedback']}")
        drafted = agent("prompts/draft-issues.md", json.dumps(reviewed))

    print(f"[escalate] {project_id}/{scan_type}: issues did not converge after {max_rounds} rounds", file=sys.stderr)
    sys.exit(1)
