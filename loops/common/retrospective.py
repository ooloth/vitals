"""Retrospective agent: analyse a completed run and post findings as issues."""

import json
import sys
from pathlib import Path

from loops.common.agent import agent
from loops.common.github import open_reflection_issues, post_reflection_findings
from loops.common.logging import log
from loops.common.logs import recent_run_dirs, write_step


def run_retrospective(
    run_dir: Path,
    reflections: list[dict],
    metadata: dict,
) -> None:
    """Run the retrospective agent and post any findings as GitHub issues."""
    context = json.dumps(
        {
            "run_metadata": metadata,
            "reflections": reflections,
            "recent_log_dirs": [str(d) for d in recent_run_dirs(limit=10) if d != run_dir],
            "open_reflection_issues": open_reflection_issues(),
        }
    )
    log.info("[retrospective] analysing run...")
    retro = agent("prompts/retrospective.md", context)
    report = retro.get("run_report", "")
    sys.stdout.write(f"\n{'═' * 60}\n{report}\n{'═' * 60}\n")
    sys.stdout.flush()
    (run_dir / "report.md").write_text(report)
    write_step(run_dir, "retrospective", retro)
    findings = retro.get("findings", [])
    if findings:
        log.info("[retrospective] posting %s finding(s)...", len(findings))
        post_reflection_findings(findings)
    else:
        log.info("[retrospective] no findings to post")
