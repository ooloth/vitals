"""Pre-flight environment checks for loop coordinators.

Validates runtime prerequisites (auth, tools, secrets, data sources) before
any agent step launches. All failures are collected and reported together so
the operator can fix everything in one pass.
"""

import os
import re
import shutil
import sys
from pathlib import Path

from loops.common.github import gh
from loops.common.logging import log
from loops.common.projects import ROOT


def _check_gh_auth() -> str | None:
    """Return an error message if the GitHub CLI is not authenticated."""
    result = gh("auth", "status", check=False)
    if result.returncode != 0:
        return "GitHub CLI is not authenticated — run `gh auth login`"
    return None


def _check_op_on_path() -> str | None:
    """Return an error message if the 1Password CLI is not on PATH."""
    if shutil.which("op") is None:
        return "1Password CLI (`op`) not found on PATH — install it or check your PATH"
    return None


def _check_secrets_env() -> str | None:
    """Return an error message if secrets.env is missing from the repo root."""
    path = ROOT / "secrets.env"
    if not path.exists():
        return f"secrets.env not found at {path} — copy secrets.env.example and fill in values"
    return None


_TOKEN_RE = re.compile(r"\$\{(\w+)}")


def _check_scan_token(scan: dict) -> str | None:
    """Return an error message if the scan's token env var is not set."""
    token_ref = scan.get("token")
    if token_ref is None:
        return None
    match = _TOKEN_RE.match(token_ref)
    if match is None:
        return None
    var_name = match.group(1)
    if os.environ.get(var_name):
        return None
    return (
        f"Environment variable {var_name} is not set"
        f" — ensure `op run --env-file=secrets.env` is wrapping the command"
    )


def _check_project_path(project: dict) -> str | None:
    """Return an error message if the project's configured path does not exist."""
    raw_path = project.get("path")
    if raw_path is None:
        return None
    resolved = Path(raw_path).expanduser().resolve()
    if resolved.is_dir():
        return None
    return f"Project path does not exist: {resolved}"


def _report_failures(errors: list[str]) -> None:
    """Log all collected errors and exit 1. No-op when the list is empty."""
    if not errors:
        log.info("[preflight] all checks passed")
        return
    log.error("[preflight] %s check(s) failed:", len(errors))
    for error in errors:
        log.error("[preflight]   ✗ %s", error)
    sys.exit(1)


def _common_checks() -> list[str]:
    """Run checks shared by all loops and return any error messages."""
    checks = [_check_gh_auth, _check_op_on_path, _check_secrets_env]
    return [msg for check in checks if (msg := check()) is not None]


def run_scan_preflight(project: dict, scan: dict) -> None:
    """Validate prerequisites for a scan run.

    Common checks plus scan-specific: token env var and project path.
    """
    errors = _common_checks()
    for check in [lambda: _check_scan_token(scan), lambda: _check_project_path(project)]:
        if msg := check():
            errors.append(msg)
    _report_failures(errors)


def run_fix_preflight(project: dict) -> None:
    """Validate prerequisites for a fix run.

    Common checks plus project path.
    """
    errors = _common_checks()
    if msg := _check_project_path(project):
        errors.append(msg)
    _report_failures(errors)


def run_groom_preflight() -> None:
    """Validate prerequisites for a groom run.

    Common checks only — groom works on issues, not the filesystem.
    """
    _report_failures(_common_checks())
