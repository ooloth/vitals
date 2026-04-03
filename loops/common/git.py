import subprocess
from pathlib import Path


def git(
    *args: str, cwd: Path, capture: bool = True, check: bool = True
) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=capture, text=True, check=check, cwd=cwd)


def default_branch(project_path: Path) -> str:
    result = git("rev-parse", "--abbrev-ref", "origin/HEAD", cwd=project_path, check=False)
    ref = result.stdout.strip()  # e.g. "origin/main" or "origin/trunk"
    if ref and "/" in ref:
        return ref.split("/", 1)[1]
    return "main"


def get_diff(branch: str, project_path: Path) -> str:
    base = default_branch(project_path)
    result = git("diff", f"{base}...{branch}", cwd=project_path)
    return result.stdout.strip() or "(no diff — branch may not exist or no changes were made)"


def prepare_branch(issue_number: int, project_path: Path) -> str:
    """Ensure working tree is clean, pull latest, and create the fix branch."""
    if git("status", "--porcelain", cwd=project_path).stdout.strip():
        raise RuntimeError(
            f"Working tree in {project_path} is dirty — resolve before running fix loop"
        )

    branch = f"fix/issue-{issue_number}"
    if git("branch", "--list", branch, cwd=project_path).stdout.strip():
        raise RuntimeError(
            f"Branch {branch!r} already exists in {project_path} — delete it manually before retrying"
        )

    base = default_branch(project_path)
    git("checkout", base, cwd=project_path)
    git("pull", "--ff-only", cwd=project_path)
    git("checkout", "-b", branch, cwd=project_path)
    print(f"[fix] created branch {branch!r} from {base}", flush=True)
    return branch


def commit_if_dirty(message: str, project_path: Path) -> bool:
    """Stage and commit any uncommitted changes. Returns True if a commit was made."""
    if not git("status", "--porcelain", cwd=project_path).stdout.strip():
        return False
    git("add", "-A", cwd=project_path)
    git("commit", "-m", message, cwd=project_path)
    print(f"[fix] committed: {message!r}", flush=True)
    return True
