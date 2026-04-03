import json
import shlex
import subprocess
import sys
from pathlib import Path

from loops.common import ROOT, agent, load_project

IMPLEMENT_TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
REVIEW_TOOLS = ["Read", "Glob", "Grep"]


def run_command(cmd: str, project_path: Path, label: str) -> None:
    print(f"[fix] {label}...", flush=True)
    result = subprocess.run(shlex.split(cmd), cwd=project_path)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed (exit {result.returncode})")


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


def run_tests(project_path: Path, test_cmd: str | None = None) -> dict:
    if test_cmd:
        result = subprocess.run(shlex.split(test_cmd), capture_output=True, text=True, cwd=project_path)
        return {"ran": True, "passed": result.returncode == 0, "output": (result.stdout + result.stderr).strip()}
    has_tests = (project_path / "tests").exists() or (project_path / "pytest.ini").exists()
    if not has_tests:
        return {"ran": False, "reason": "no test suite found"}
    venv_python = project_path / ".venv" / "bin" / "python"
    python = str(venv_python) if venv_python.exists() else "python3"
    result = subprocess.run(
        [python, "-m", "pytest", "--tb=short", "-q"],
        capture_output=True, text=True, cwd=project_path,
    )
    return {"ran": True, "passed": result.returncode == 0, "output": (result.stdout + result.stderr).strip()}


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


def commit_if_dirty(message: str, project_path: Path) -> bool:
    """Stage and commit any uncommitted changes. Returns True if a commit was made."""
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, check=True, cwd=project_path,
    )
    if not status.stdout.strip():
        return False
    subprocess.run(["git", "add", "-A"], check=True, capture_output=True, cwd=project_path)
    subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True, cwd=project_path)
    print(f"[fix] committed: {message!r}", flush=True)
    return True


def open_pr(branch: str, impl: dict, project_path: Path) -> None:
    subprocess.run(["git", "push", "-u", "origin", branch], check=True, cwd=project_path)
    subprocess.run([
        "gh", "pr", "create",
        "--title", impl["pr_title"],
        "--body", impl["pr_body"],
        "--head", branch,
    ], check=True, cwd=project_path)


def run_fix(issue_number: int | None = None, project_id: str | None = None, max_rounds: int = 10) -> None:
    project = load_project(project_id) if project_id else {}
    project_path = Path(project["path"]) if project else ROOT

    original_branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, check=True, cwd=project_path,
    ).stdout.strip()

    if issue_number is None:
        issue_number = next_open_issue()
    if issue_number is None:
        print("[fix] no open issues to fix")
        return

    print(f"[fix] issue #{issue_number} in {project_path}", flush=True)

    for key, label in [("install", "installing dependencies"), ("checks", "running checks"), ("tests", "running tests")]:
        if cmd := project.get(key):
            run_command(cmd, project_path, label)

    try:
        branch = prepare_branch(issue_number, project_path)
        issue = json.dumps({
            "issue": json.loads(issue_context(issue_number)),
            "branch": branch,
        })

        for round_n in range(max_rounds):
            print(f"[fix] round {round_n + 1}: implementing...", flush=True)
            impl = agent("prompts/implement.md", issue, allowed_tools=IMPLEMENT_TOOLS)

            commit_if_dirty(impl.get("pr_title", f"fix: issue #{issue_number}"), project_path)

            diff = get_diff(branch, project_path)
            if not diff or diff.startswith("(no diff"):
                print(f"[fix] round {round_n + 1}: no diff on {branch!r} — treating as revision needed", flush=True)
                issue = json.dumps({
                    "issue": json.loads(issue_context(issue_number)),
                    "branch": branch,
                    "feedback": f"Branch {branch!r} has no diff against the base branch. You must make changes and ensure they are committed.",
                })
                continue

            tests = run_tests(project_path, project.get("tests"))

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

    finally:
        subprocess.run(["git", "checkout", original_branch], cwd=project_path, capture_output=True)
