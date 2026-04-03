import json
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent

IMPLEMENT_TOOLS = ["Bash(git:*)", "Read", "Write", "Edit", "Glob", "Grep"]
REVIEW_TOOLS = ["Read", "Glob", "Grep"]


def agent(prompt_file: str, context: str, max_turns: int = 20, allowed_tools: list[str] | None = None) -> dict:
    prompt = (ROOT / prompt_file).read_text()
    output_file = Path(tempfile.mktemp(suffix=".json"))
    full_prompt = (
        f"{context}\n\n---\n\n{prompt}\n\n"
        f"Write your JSON output to this file: {output_file}\n"
        f"Do not include the JSON in your text response."
    )
    cmd = ["claude", "-p", full_prompt, "--max-turns", str(max_turns)]
    if allowed_tools:
        cmd += ["--allowedTools"] + allowed_tools
    print(f"\n{'─' * 60}", flush=True)
    result = subprocess.run(cmd, cwd=ROOT, capture_output=False)
    print(f"{'─' * 60}", flush=True)
    if result.returncode != 0:
        raise RuntimeError(f"claude subprocess exited with return code {result.returncode}")
    if not output_file.exists():
        raise RuntimeError(f"Agent did not write output to {output_file}")
    result = json.loads(output_file.read_text())
    output_file.unlink()
    return result


def load_project_path(project_id: str) -> Path:
    config = tomllib.loads((ROOT / "projects/projects.toml").read_text())
    project = next((p for p in config["projects"] if p["id"] == project_id), None)
    if project is None:
        raise ValueError(f"Project '{project_id}' not found in projects.toml")
    if "path" not in project:
        raise ValueError(f"Project '{project_id}' has no 'path' in projects.toml")
    return Path(project["path"]).expanduser().resolve()


def next_open_issue() -> int | None:
    result = subprocess.run(
        ["gh", "issue", "list", "--label", "agent", "--json", "number", "--limit", "1"],
        capture_output=True, text=True, check=True,
    )
    issues = json.loads(result.stdout)
    return issues[0]["number"] if issues else None


def issue_context(issue_number: int) -> str:
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--json", "number,title,body,labels"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def default_branch(project_path: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "origin/HEAD"],
        capture_output=True, text=True, cwd=project_path,
    )
    ref = result.stdout.strip()  # e.g. "origin/main" or "origin/trunk"
    if ref and "/" in ref:
        return ref.split("/", 1)[1]
    return "main"


def get_diff(branch: str, project_path: Path) -> str:
    base = default_branch(project_path)
    result = subprocess.run(
        ["git", "diff", f"{base}...{branch}"],
        capture_output=True, text=True, cwd=project_path,
    )
    return result.stdout.strip() or "(no diff — branch may not exist or no changes were made)"


def run_tests(project_path: Path) -> dict:
    has_tests = (project_path / "tests").exists() or (project_path / "pytest.ini").exists()
    if not has_tests:
        return {"ran": False, "reason": "no test suite found"}
    result = subprocess.run(
        ["python3", "-m", "pytest", "--tb=short", "-q"],
        capture_output=True, text=True, cwd=project_path,
    )
    return {
        "ran": True,
        "passed": result.returncode == 0,
        "output": (result.stdout + result.stderr).strip(),
    }


def prepare_branch(issue_number: int, project_path: Path) -> str:
    """Ensure working tree is clean, pull latest, and create the fix branch."""
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, check=True, cwd=project_path,
    )
    if dirty.stdout.strip():
        raise RuntimeError(
            f"Working tree in {project_path} is dirty — resolve before running fix loop"
        )

    branch = f"fix/issue-{issue_number}"
    existing = subprocess.run(
        ["git", "branch", "--list", branch],
        capture_output=True, text=True, check=True, cwd=project_path,
    )
    if existing.stdout.strip():
        raise RuntimeError(
            f"Branch {branch!r} already exists in {project_path} — delete it manually before retrying"
        )

    base = default_branch(project_path)
    subprocess.run(["git", "checkout", base], check=True, capture_output=True, cwd=project_path)
    subprocess.run(["git", "pull", "--ff-only"], check=True, capture_output=True, cwd=project_path)
    subprocess.run(["git", "checkout", "-b", branch], check=True, capture_output=True, cwd=project_path)
    print(f"[fix] created branch {branch!r} from {base}", flush=True)
    return branch


def open_pr(branch: str, impl: dict, project_path: Path) -> None:
    subprocess.run([
        "gh", "pr", "create",
        "--title", impl["pr_title"],
        "--body", impl["pr_body"],
        "--head", branch,
    ], check=True, cwd=project_path)


def run_fix(issue_number: int | None = None, project_id: str | None = None, max_rounds: int = 10) -> None:
    project_path = load_project_path(project_id) if project_id else ROOT

    if issue_number is None:
        issue_number = next_open_issue()
    if issue_number is None:
        print("[fix] no open issues to fix")
        return

    print(f"[fix] issue #{issue_number} in {project_path}", flush=True)
    branch = prepare_branch(issue_number, project_path)
    issue = json.dumps({
        "issue": json.loads(issue_context(issue_number)),
        "branch": branch,
    })

    for round_n in range(max_rounds):
        print(f"[fix] round {round_n + 1}: implementing...", flush=True)
        impl = agent("prompts/implement.md", issue, allowed_tools=IMPLEMENT_TOOLS)

        diff = get_diff(branch, project_path)
        if not diff or diff.startswith("(no diff"):
            print(f"[fix] round {round_n + 1}: no diff on {branch!r} — treating as revision needed", flush=True)
            issue = json.dumps({
                "issue": json.loads(issue_context(issue_number)),
                "branch": branch,
                "feedback": f"Branch {branch!r} has no diff against the base branch. You must commit your changes before reporting back.",
            })
            continue

        tests = run_tests(project_path)

        review_context = json.dumps({
            "issue": json.loads(issue_context(issue_number)),
            "implementation": impl,
            "diff": diff,
            "tests": tests,
        })

        print(f"[fix] round {round_n + 1}: reviewing...", flush=True)
        reviewed = agent("prompts/review.md", review_context, allowed_tools=REVIEW_TOOLS)

        if reviewed["approved"]:
            open_pr(branch, impl, project_path)
            print(f"[fix] issue #{issue_number}: PR opened ({impl['pr_title']})")
            return

        print(f"[fix] round {round_n + 1}: revision needed — {reviewed['feedback']}", flush=True)
        issue = json.dumps({
            "issue": json.loads(issue_context(issue_number)),
            "branch": branch,
            "feedback": reviewed["feedback"],
        })

    print(f"[escalate] issue #{issue_number}: did not converge after {max_rounds} rounds", file=sys.stderr)
    sys.exit(1)
