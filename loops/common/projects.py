import json
import shlex
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


def load_project(project_id: str) -> dict:
    config = json.loads((ROOT / "projects/projects.json").read_text())
    project = next((p for p in config["projects"] if p["id"] == project_id), None)
    if project is None:
        raise ValueError(f"Project '{project_id}' not found in projects.json")
    if "path" in project:
        project["path"] = str(Path(project["path"]).expanduser().resolve())
    return project


def scan_context(project: dict, scan: dict) -> str:
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
    print(f"[fix] {label}...", flush=True)
    result = subprocess.run(shlex.split(cmd), cwd=project_path)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed (exit {result.returncode})")


def run_tests(project_path: Path, test_cmd: str | None = None) -> dict:
    if test_cmd:
        result = subprocess.run(
            shlex.split(test_cmd), capture_output=True, text=True, cwd=project_path
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
    result = subprocess.run(
        [python, "-m", "pytest", "--tb=short", "-q"],
        capture_output=True,
        text=True,
        cwd=project_path,
    )
    return {
        "ran": True,
        "passed": result.returncode == 0,
        "output": (result.stdout + result.stderr).strip(),
    }
