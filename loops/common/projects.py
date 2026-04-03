import shlex
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


def load_project(project_id: str) -> dict:
    config = tomllib.loads((ROOT / "projects/projects.toml").read_text())
    project = next((p for p in config["projects"] if p["id"] == project_id), None)
    if project is None:
        raise ValueError(f"Project '{project_id}' not found in projects.toml")
    if "path" in project:
        project["path"] = str(Path(project["path"]).expanduser().resolve())
    return project


def project_context(project_id: str) -> str:
    import json
    project = load_project(project_id)
    context_path = ROOT / f"projects/{project_id}/context.md"
    context = context_path.read_text() if context_path.exists() else ""
    return f"Project config:\n{json.dumps(project, indent=2)}\n\nProject context:\n{context}"


def run_command(cmd: str, project_path: Path, label: str) -> None:
    print(f"[fix] {label}...", flush=True)
    result = subprocess.run(shlex.split(cmd), cwd=project_path)
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed (exit {result.returncode})")


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
