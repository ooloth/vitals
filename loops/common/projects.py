"""Project config loading, context building, and command/test runners."""

import json
import os
import subprocess
from pathlib import Path

from loops.common.logging import log

ROOT = Path(__file__).parent.parent.parent


def load_project(project_id: str) -> dict:
    """Load and return the project config dict for the given project ID."""
    config = json.loads((ROOT / "projects/projects.json").read_text())
    project = next((p for p in config["projects"] if p["id"] == project_id), None)
    if project is None:
        msg = f"Project '{project_id}' not found in projects.json"
        raise ValueError(msg)
    if "path" in project:
        project["path"] = str(Path(project["path"]).expanduser().resolve())
    return project


def scan_context(project: dict, scan: dict) -> str:
    """Build a plain-text context string describing what to scan and how to interpret it."""
    meta = {k: v for k, v in project.items() if k != "scans"}
    lines = [
        f"Project: {project['name']}",
        f"Config: {json.dumps(meta, indent=2)}",
        "",
        "What is normal for this scan:",
        *[f"- {item}" for item in scan["normal"]],
        "",
        "What to flag:",
        *[f"- {item}" for item in scan["flag"]],
        "",
        "What to ignore:",
        *[f"- {item}" for item in scan["ignore"]],
    ]
    return "\n".join(lines)


def run_command(cmd: str, project_path: Path, label: str) -> None:
    """Run an arbitrary shell command and raise RuntimeError on non-zero exit."""
    log.info("[fix] %s...", label)
    env = {**os.environ, "_CMD": cmd}
    result = subprocess.run(
        ["/bin/sh", "-c", "$_CMD"],
        env=env,
        cwd=project_path,
        check=False,
    )
    if result.returncode != 0:
        msg = f"{label} failed (exit {result.returncode})"
        raise RuntimeError(msg)


def run_tests(project_path: Path, test_cmd: str | None = None) -> dict:
    """Run the project's test suite and return a result dict with ran/passed/output."""
    if test_cmd:
        env = {**os.environ, "_CMD": test_cmd}
        result = subprocess.run(
            ["/bin/sh", "-c", "$_CMD"],
            capture_output=True,
            text=True,
            check=False,
            cwd=project_path,
            env=env,
        )
        return {
            "ran": True,
            "passed": result.returncode == 0,
            "output": (result.stdout + result.stderr).strip(),
        }
    has_tests = (project_path / "tests").exists() or (project_path / "pytest.ini").exists()
    if not has_tests:
        return {"ran": False, "reason": "no test suite found"}
    venv_python = project_path / ".venv" / "bin" / "python"
    python = str(venv_python) if venv_python.exists() else "python3"
    env = {**os.environ, "_PYTHON": python}
    result = subprocess.run(
        ["/bin/sh", "-c", '"$_PYTHON" -m pytest --tb=short -q'],
        capture_output=True,
        text=True,
        check=False,
        cwd=project_path,
        env=env,
    )
    return {
        "ran": True,
        "passed": result.returncode == 0,
        "output": (result.stdout + result.stderr).strip(),
    }
