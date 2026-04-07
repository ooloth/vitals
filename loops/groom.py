"""Groom loop: evaluate open issues against the current codebase.

Fetches all open autonomous issues, runs the freshness evaluate agent on
each one, and applies the verdict: no change if still present, edit the
body if partially resolved, close with a comment if fully resolved.
"""

import json
import time
from pathlib import Path

from loops.common import (
    AgentConfig,
    agent,
    close_issue,
    edit_issue_body,
    load_project,
    log,
    make_run_dir,
    open_autonomous_issues,
    run_groom_preflight,
    write_step,
)

_EVALUATE_PROMPT = "prompts/scan/agency/issues/freshness.md"
_EVALUATE_CFG = AgentConfig(
    allowed_tools=["Read", "Glob", "Grep"],
    max_turns=30,
)


def _step(
    run_dir: Path,
    steps: list[dict],
    refs: list[dict],
    name: str,
    content: str,
) -> dict:
    """Run one evaluate step: time it, persist output, collect reflections."""
    t0 = time.monotonic()
    cfg = AgentConfig(
        allowed_tools=_EVALUATE_CFG.allowed_tools,
        max_turns=_EVALUATE_CFG.max_turns,
        transcript_path=run_dir / f"{name}-transcript.jsonl",
        step_name=name,
    )
    out = agent(_EVALUATE_PROMPT, content, cfg)
    steps.append({"name": name, "duration_seconds": round(time.monotonic() - t0, 1)})
    write_step(run_dir, name, out)
    refs.extend({"step": name, "text": r} for r in out.get("reflections", []))
    return out


def _apply_verdict(verdict: dict, issue_number: int, *, dry_run: bool) -> None:
    """Apply a single freshness verdict to an issue."""
    match verdict["verdict"]:
        case "present":
            log.info("[groom] #%s: still present — no change", issue_number)
        case "partial":
            if dry_run:
                log.info("[groom] #%s: partially resolved — would edit body", issue_number)
            else:
                edit_issue_body(issue_number, verdict["updated_body"])
                log.info("[groom] #%s: partially resolved — body updated", issue_number)
        case "resolved":
            if dry_run:
                log.info("[groom] #%s: fully resolved — would close", issue_number)
            else:
                close_issue(issue_number, f"Closed by groom: {verdict['summary']}")
                log.info("[groom] #%s: fully resolved — closed", issue_number)
        case other:
            log.warning("[groom] #%s: unknown verdict %r — skipping", issue_number, other)


def run_groom(project_id: str, *, dry_run: bool = False) -> None:
    """Evaluate all open autonomous issues for freshness against the current codebase."""
    project = load_project(project_id)
    run_groom_preflight()
    project_meta = {k: v for k, v in project.items() if k != "scans"}

    issues = open_autonomous_issues()
    if not issues:
        log.info("[groom] no open autonomous issues to evaluate")
        return

    log.info("[groom] evaluating %s open issue(s)...", len(issues))
    run_dir = make_run_dir(f"groom-{project_id}")
    steps: list[dict] = []
    refs: list[dict] = []
    started_at = time.monotonic()

    for issue in issues:
        issue_number = issue["number"]
        content = json.dumps({"issue": issue, "project": project_meta})
        log.info("[groom] evaluating #%s: %s", issue_number, issue["title"])
        verdict = _step(run_dir, steps, refs, f"evaluate-{issue_number}", content)
        _apply_verdict(verdict, issue_number, dry_run=dry_run)

    metadata = {
        "run_type": "groom",
        "project_id": project_id,
        "dry_run": dry_run,
        "duration_seconds": round(time.monotonic() - started_at, 1),
        "steps": steps,
        "issues_evaluated": len(issues),
    }
    write_step(run_dir, "metadata", metadata)
    write_step(run_dir, "reflections", refs)
