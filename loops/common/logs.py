"""Run log directory helpers for persisting step outputs and retrospective reports."""

import json
from datetime import UTC, datetime
from pathlib import Path

from loops.common.projects import ROOT

LOGS_DIR = ROOT / ".logs"


def make_run_dir(label: str) -> Path:
    """Create and return a timestamped directory under .logs/ for this run."""
    timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d-%H-%M")
    run_dir = LOGS_DIR / f"{timestamp}-{label}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_step(run_dir: Path, step_name: str, output: dict | list) -> None:
    """Write a step's JSON output to the run directory."""
    (run_dir / f"{step_name}.json").write_text(json.dumps(output, indent=2))
