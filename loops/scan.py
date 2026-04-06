"""Agentic scan loop: find problems, triage, draft issues, review, and post."""

import dataclasses
import json
import sys
import time
from pathlib import Path

from loops.common import (
    agent,
    approved_issue_count,
    load_project,
    log,
    make_run_dir,
    post_issues,
    recent_run_summaries,
    scan_context,
    write_step,
)

BACKPRESSURE_CAP = 10


@dataclasses.dataclass
class _RunCtx:
    run_dir: Path
    steps: list[dict]
    refs: list[dict]
    extra_labels: list[str]


@dataclasses.dataclass
class _StepCfg:
    # Find steps are read-only analysis: explicit list prevents silent Bash
    # denial in non-interactive -p mode (see decision 08). Triage/draft/review
    # steps work on JSON input and need no tools, so None is fine.
    allowed_tools: list[str] | None = None
    # Higher ceiling for find: docs-heavy scans need many reads.
    max_turns: int = 20


_FIND_CFG = _StepCfg(allowed_tools=["Read", "Glob", "Grep"], max_turns=30)


def _issue_labels(scan_type: str) -> list[str]:
    """Return the labels to apply to every issue posted by this scan type."""
    if scan_type == "agency/retrospective":
        source = "scan:retrospective"
    elif scan_type == "agency/fix-retrospective":
        source = "fix:retrospective"
    elif scan_type.startswith("logs/"):
        source = "scan:logs"
    else:
        source = "scan:codebase"
    return ["autonomous", "needs-human-review", source]


def _step(
    ctx: _RunCtx,
    name: str,
    prompt: str,
    content: str,
    cfg: _StepCfg | None = None,
) -> dict:
    """Run one agent step: time it, persist output, collect reflections."""
    cfg = cfg or _StepCfg()
    t0 = time.monotonic()
    out = agent(
        prompt,
        content,
        max_turns=cfg.max_turns,
        allowed_tools=cfg.allowed_tools,
        transcript_path=ctx.run_dir / f"{name}-transcript.jsonl",
    )
    ctx.steps.append({"name": name, "duration_seconds": round(time.monotonic() - t0, 1)})
    write_step(ctx.run_dir, name, out)
    ctx.refs.extend({"step": name, "text": r} for r in out.get("reflections", []))
    return out


def _run_review_rounds(
    ctx: _RunCtx,
    drafted: dict,
    max_rounds: int,
    label: str,
    *,
    dry_run: bool,
) -> bool:
    """Run review/redraft rounds. Returns True if issues converged and were posted."""
    for round_n in range(max_rounds):
        log.info("[scan] reviewing issues (round %s)...", round_n + 1)
        reviewed = _step(
            ctx,
            f"review-{round_n + 1}",
            "prompts/scan/review-issues.md",
            json.dumps(drafted),
        )
        if reviewed["ready"]:
            post_issues(reviewed["issues"], extra_labels=ctx.extra_labels, dry_run=dry_run)
            action = "would post" if dry_run else "posted"
            log.info("[scan] %s: %s %s issue(s)", label, action, len(reviewed["issues"]))
            return True
        log.info("[scan] round %s: needs revision — %s", round_n + 1, reviewed["feedback"])
        drafted = _step(
            ctx,
            f"redraft-{round_n + 1}",
            "prompts/scan/draft-issues.md",
            json.dumps(reviewed),
        )
    return False


def run_scan(
    project_id: str, scan_type: str = "logs", max_rounds: int = 5, *, dry_run: bool = False
) -> None:
    """Scan a project for problems and post issues, respecting the backpressure cap."""
    if not dry_run:
        open_count = approved_issue_count()
        if open_count >= BACKPRESSURE_CAP:
            log.info(
                "[scan] %s open issues pending fix — skipping scan (backpressure cap: %s)",
                open_count,
                BACKPRESSURE_CAP,
            )
            return

    project = load_project(project_id)
    scan = next((s for s in project["scans"] if s["type"] == scan_type), None)
    if scan is None:
        msg = f"Project '{project_id}' has no '{scan_type}' scan configured"
        raise ValueError(msg)
    context = scan_context(project, scan)
    if scan_type in ("agency/retrospective", "agency/fix-retrospective"):
        summaries = recent_run_summaries()
        context = f"{context}\n\n## Recent run summaries\n\n{json.dumps(summaries, indent=2)}"

    run_dir = make_run_dir(f"{project_id}-{scan_type.replace('/', '-')}")
    ctx = _RunCtx(run_dir=run_dir, steps=[], refs=[], extra_labels=_issue_labels(scan_type))
    started_at = time.monotonic()
    converged = False
    exit_code = 0

    try:
        log.info("[scan] %s/%s: finding problems...", project_id, scan_type)
        raw = _step(ctx, "find", f"prompts/scan/sources/{scan_type}.md", context, _FIND_CFG)

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

        converged = _run_review_rounds(
            ctx, drafted, max_rounds, f"{project_id}/{scan_type}", dry_run=dry_run
        )
        if not converged:
            log.error(
                "[escalate] %s/%s: issues did not converge after %s rounds",
                project_id,
                scan_type,
                max_rounds,
            )
            exit_code = 1

    finally:
        if not converged:
            exit_code = max(exit_code, 1)
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
        write_step(run_dir, "metadata", metadata)
        write_step(run_dir, "reflections", ctx.refs)
        if exit_code != 0 and sys.exc_info()[0] is None:
            sys.exit(exit_code)
