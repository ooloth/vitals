"""Git subprocess wrapper using shlex-quoted env vars to avoid untrusted input."""

import os
import shlex
import subprocess
from pathlib import Path

from loops.common.logging import log


def git(
    *args: str, cwd: Path, capture: bool = True, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a git command with the given arguments."""
    env = {**os.environ, "_GIT_ARGS": shlex.join(args)}
    return subprocess.run(
        ["/bin/sh", "-c", "eval git $_GIT_ARGS"],
        capture_output=capture,
        text=True,
        check=check,
        cwd=cwd,
        env=env,
    )


def default_branch(project_path: Path) -> str:
    """Return the default branch name (e.g. main, trunk) for the given repo."""
    result = git("rev-parse", "--abbrev-ref", "origin/HEAD", cwd=project_path, check=False)
    ref = result.stdout.strip()  # e.g. "origin/main" or "origin/trunk"
    if ref and "/" in ref:
        return ref.split("/", 1)[1]
    return "main"


def get_diff(branch: str, project_path: Path) -> str:
    """Return the git diff between the default branch and the given branch."""
    base = default_branch(project_path)
    result = git("diff", f"{base}...{branch}", cwd=project_path)
    return result.stdout.strip() or "(no diff — branch may not exist or no changes were made)"


def prepare_branch(issue_number: int, project_path: Path) -> str:
    """Ensure working tree is clean, pull latest, and create the fix branch."""
    if git("status", "--porcelain", cwd=project_path).stdout.strip():
        msg = f"Working tree in {project_path} is dirty — resolve before running fix loop"
        raise RuntimeError(msg)

    branch = f"fix/issue-{issue_number}"
    if git("branch", "--list", branch, cwd=project_path).stdout.strip():
        msg = (
            f"Branch {branch!r} already exists in {project_path}"
            " — delete it manually before retrying"
        )
        raise RuntimeError(msg)

    base = default_branch(project_path)
    git("checkout", base, cwd=project_path)
    git("pull", "--ff-only", cwd=project_path)
    git("checkout", "-b", branch, cwd=project_path)
    log.info("[fix] created branch %r from %s", branch, base)
    return branch


def commit_if_dirty(message: str, project_path: Path) -> bool:
    """Stage and commit any uncommitted changes. Returns True if a commit was made."""
    if not git("status", "--porcelain", cwd=project_path).stdout.strip():
        return False
    git("add", "-A", cwd=project_path)
    git("commit", "-m", message, cwd=project_path)
    log.info("[fix] committed: %r", message)
    return True
