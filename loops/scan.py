import json
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _parse_result(text: str) -> dict:
    # strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text.strip())


def agent(prompt_file: str, context: str) -> dict:
    prompt = (ROOT / prompt_file).read_text()
    envelope = subprocess.run(
        ["claude", "-p", f"{context}\n\n---\n\n{prompt}", "--output-format", "json"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    outer = json.loads(envelope.stdout)
    return _parse_result(outer["result"])


def project_context(project_id: str) -> str:
    config = tomllib.loads((ROOT / "projects/projects.toml").read_text())
    project = next(p for p in config["projects"] if p["id"] == project_id)
    context_path = ROOT / f"projects/{project_id}/context.md"
    context = context_path.read_text() if context_path.exists() else ""
    return f"Project config:\n{json.dumps(project, indent=2)}\n\nProject context:\n{context}"


def post_issues(issues: list[dict], dry_run: bool = False) -> None:
    for issue in issues:
        if dry_run:
            print(f"\n[dry-run] would post issue:")
            print(f"  title: {issue['title']}")
            print(f"  label: {issue.get('label', 'sev:medium')}")
            print(f"  body:\n{issue['body']}\n")
        else:
            subprocess.run([
                "gh", "issue", "create",
                "--title", issue["title"],
                "--body", issue["body"],
                "--label", issue.get("label", "sev:medium"),
            ], check=True)


def run_scan(project_id: str, scan_type: str = "logs", max_rounds: int = 5, dry_run: bool = False) -> None:
    context = project_context(project_id)

    print(f"[scan] {project_id}/{scan_type}: finding problems...")
    raw = agent(f"prompts/scans/{scan_type}.md", context)

    if not raw.get("findings"):
        print(f"[scan] {project_id}/{scan_type}: nothing to report")
        return

    print(f"[scan] {len(raw['findings'])} finding(s) — triaging...")
    clustered = agent("prompts/triage.md", json.dumps(raw))

    if not clustered.get("clusters"):
        print(f"[scan] {project_id}/{scan_type}: no actionable clusters after triage")
        return

    print(f"[scan] {len(clustered['clusters'])} cluster(s) — drafting issues...")
    drafted = agent("prompts/draft-issues.md", json.dumps(clustered))

    for round_n in range(max_rounds):
        print(f"[scan] reviewing issues (round {round_n + 1})...")
        reviewed = agent("prompts/review-issues.md", json.dumps(drafted))
        if reviewed["ready"]:
            post_issues(reviewed["issues"], dry_run=dry_run)
            print(f"[scan] {project_id}/{scan_type}: {'would post' if dry_run else 'posted'} {len(reviewed['issues'])} issue(s)")
            return
        print(f"[scan] round {round_n + 1}: needs revision — {reviewed['feedback']}")
        drafted = agent("prompts/draft-issues.md", json.dumps(reviewed))

    print(f"[escalate] {project_id}/{scan_type}: issues did not converge after {max_rounds} rounds", file=sys.stderr)
    sys.exit(1)
