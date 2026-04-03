import json
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent


def agent(prompt_file: str, context: str, max_turns: int = 15) -> dict:
    prompt = (ROOT / prompt_file).read_text()
    output_file = Path(tempfile.mktemp(suffix=".json"))
    full_prompt = (
        f"{context}\n\n---\n\n{prompt}\n\n"
        f"Write your JSON output to this file: {output_file}\n"
        f"Do not include the JSON in your text response."
    )
    print(f"\n{'─' * 60}", flush=True)
    subprocess.run(
        ["claude", "-p", full_prompt, "--max-turns", str(max_turns)],
        cwd=ROOT,
    )
    print(f"{'─' * 60}", flush=True)
    if not output_file.exists():
        raise RuntimeError(f"Agent did not write output to {output_file}")
    result = json.loads(output_file.read_text())
    output_file.unlink()
    return result


def load_project(project_id: str) -> dict:
    config = tomllib.loads((ROOT / "projects/projects.toml").read_text())
    project = next((p for p in config["projects"] if p["id"] == project_id), None)
    if project is None:
        raise ValueError(f"Project '{project_id}' not found in projects.toml")
    if "path" in project:
        project["path"] = str(Path(project["path"]).expanduser().resolve())
    return project


def project_context(project_id: str) -> str:
    project = load_project(project_id)
    context_path = ROOT / f"projects/{project_id}/context.md"
    context = context_path.read_text() if context_path.exists() else ""
    return f"Project config:\n{json.dumps(project, indent=2)}\n\nProject context:\n{context}"


BACKPRESSURE_CAP = 10


def open_issue_titles() -> set[str]:
    result = subprocess.run(
        ["gh", "issue", "list", "--label", "agent", "--json", "title", "--limit", "100"],
        capture_output=True, text=True, check=True,
    )
    return {i["title"] for i in json.loads(result.stdout)}


def post_issues(issues: list[dict], dry_run: bool = False) -> None:
    existing = set() if dry_run else open_issue_titles()
    for issue in issues:
        title = issue["title"]
        if title in existing:
            print(f"[scan] skipping duplicate: {title!r}")
            continue
        if dry_run:
            print(f"\n[dry-run] would post issue:")
            print(f"  title: {title}")
            print(f"  label: {issue.get('label', 'sev:medium')}")
            print(f"  body:\n{issue['body']}\n")
        else:
            subprocess.run([
                "gh", "issue", "create",
                "--title", title,
                "--body", issue["body"],
                "--label", issue.get("label", "sev:medium"),
            ], check=True)


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
