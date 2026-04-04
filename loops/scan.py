"""Agentic scan loop: find problems, triage, draft issues, review, and post."""

import dataclasses
import json
import sys
import time
from pathlib import Path

from loops.common import (
    agent,
    load_project,
    log,
    make_run_dir,
    open_issue_titles,
    post_issues,
    run_retrospective,
    scan_context,
    write_step,
)

BACKPRESSURE_CAP = 10


@dataclasses.dataclass
class _RunCtx:
    run_dir: Path
    steps: list[dict]
    refs: list[dict]


def _step(ctx: _RunCtx, name: str, prompt: str, content: str) -> dict:
    """Run one agent step: time it, persist output, collect reflections."""
    t0 = time.monotonic()
    out = agent(prompt, content)
    ctx.steps.append({"name": name, "duration_seconds": round(time.monotonic() - t0, 1)})
    write_step(ctx.run_dir, name, out)
    ctx.refs.extend({"step": name, "text": r} for r in out.get("reflections", []))
    return out


def run_scan(
    project_id: str, scan_type: str = "logs", max_rounds: int = 5, *, dry_run: bool = False
) -> None:
    """Scan a project for problems and post issues, respecting the backpressure cap."""
    if not dry_run:
        open_count = len(open_issue_titles())
        if open_count >= BACKPRESSURE_CAP:
            log.info(
                "[scan] %s open issues pending fix — skipping scan (backpressure cap: %s)",
                open_count,
                BACKPRESSURE_CAP,
            )
            return

    run_label = f"{project_id}-{scan_type.replace('/', '-')}"
    run_dir = make_run_dir(run_label)
    ctx = _RunCtx(run_dir=run_dir, steps=[], refs=[])
    started_at = time.monotonic()
    converged = False
    exit_code = 0

    try:
        project = load_project(project_id)
        scan = next((s for s in project["scans"] if s["type"] == scan_type), None)
        if scan is None:
            msg = f"Project '{project_id}' has no '{scan_type}' scan configured"
            raise ValueError(msg)
        context = scan_context(project, scan)

        log.info("[scan] %s/%s: finding problems...", project_id, scan_type)
        raw = _step(ctx, "find", f"prompts/scan/sources/{scan_type}.md", context)

        if not raw.get("findings"):
            log.info("[scan] %s/%s: nothing to report", project_id, scan_type)
            converged = True
            return

        log.info("[scan] %s finding(s) — triaging...", len(raw["findings"]))
        clustered = _step(ctx, "triage", "prompts/scan/triage.md", json.dumps(raw))

        if not clustered.get("clusters"):
            log.info("[scan] %s/%s: no actionable clusters after triage", project_id, scan_type)
            converged = True
            return

        log.info("[scan] %s cluster(s) — drafting issues...", len(clustered["clusters"]))
        drafted = _step(ctx, "draft", "prompts/scan/draft-issues.md", json.dumps(clustered))

        for round_n in range(max_rounds):
            log.info("[scan] reviewing issues (round %s)...", round_n + 1)
            reviewed = _step(
                ctx,
                f"review-{round_n + 1}",
                "prompts/scan/review-issues.md",
                json.dumps(drafted),
            )
            if reviewed["ready"]:
                post_issues(reviewed["issues"], dry_run=dry_run)
                action = "would post" if dry_run else "posted"
                log.info(
                    "[scan] %s/%s: %s %s issue(s)",
                    project_id,
                    scan_type,
                    action,
                    len(reviewed["issues"]),
                )
                converged = True
                return
            log.info("[scan] round %s: needs revision — %s", round_n + 1, reviewed["feedback"])
            drafted = _step(
                ctx,
                f"redraft-{round_n + 1}",
                "prompts/scan/draft-issues.md",
                json.dumps(reviewed),
            )

        log.error(
            "[escalate] %s/%s: issues did not converge after %s rounds",
            project_id,
            scan_type,
            max_rounds,
        )
        exit_code = 1

    finally:
        metadata = {
            "run_type": "scan",
            "project_id": project_id,
            "scan_type": scan_type,
            "dry_run": dry_run,
            "duration_seconds": round(time.monotonic() - started_at, 1),
            "steps": ctx.steps,
            "converged": converged,
            "exit_code": exit_code,
        }
        run_retrospective(run_dir, ctx.refs, metadata, dry_run=dry_run)
        if exit_code != 0:
            sys.exit(exit_code)
