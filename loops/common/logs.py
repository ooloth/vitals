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


def recent_run_summaries(limit: int = 20) -> list[dict]:
    """Return metadata from the most recent run directories, newest first.

    Each entry is the parsed metadata.json for that run, with an added
    ``run_dir`` key pointing at the directory (so the agent knows where to
    look for step JSONs and transcripts without a separate Glob call).
    """
    if not LOGS_DIR.exists():
        return []
    dirs = sorted(
        (d for d in LOGS_DIR.iterdir() if d.is_dir()),
        key=lambda p: p.name,
        reverse=True,
    )[:limit]
    summaries = []
    for d in dirs:
        meta_path = d / "metadata.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text())
            meta["run_dir"] = str(d)
            summaries.append(meta)
        except json.JSONDecodeError:
            pass
    return summaries
