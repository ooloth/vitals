"""Agentic scan loop: find problems, triage, draft issues, review, and post."""

import dataclasses
import json
import sys
import time
from pathlib import Path

from loops.common import (
    AgentConfig,
    approved_issue_count,
    create_issue,
    load_project,
    log,
    make_run_dir,
    post_issues,
    recent_run_summaries,
    run_scan_preflight,
    scan_context,
    step,
    write_step,
)

BACKPRESSURE_CAP = 10


@dataclasses.dataclass
class _RunCtx:
    run_dir: Path
    steps: list[dict]
    refs: list[dict]
    extra_labels: list[str]
    last_draft: dict = dataclasses.field(default_factory=dict)
    last_review_feedback: str = ""
    converged: bool = False
    exit_code: int = 0


# Find steps are read-only analysis: explicit list prevents silent Bash
# denial in non-interactive -p mode (see decision 08). Higher ceiling
# for find: docs-heavy scans need many reads.
_FIND_CFG = AgentConfig(allowed_tools=["Read", "Glob", "Grep"], max_turns=30)


def _find_prompt(scan_type: str) -> str:
    """Return the prompt path for a scan type's find step."""
    return f"prompts/scan/{scan_type}.md"


def _issue_labels(scan_type: str) -> list[str]:
    """Return the labels to apply to every issue posted by this scan type."""
    if scan_type == "agency/history/scans":
        source = "scan:retrospective"
    elif scan_type == "agency/history/fixes":
        source = "fix:retrospective"
    elif scan_type.startswith("logs/"):
        source = "scan:logs"
    else:
        source = "scan:codebase"
    return ["autonomous", "needs-human-review", source]


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
        ctx.last_draft = drafted
        log.info("[scan] reviewing issues (round %s)...", round_n + 1)
        reviewed = step(
            ctx,
            f"review-{round_n + 1}",
            "prompts/scan/review.md",
            json.dumps(drafted),
        )
        if reviewed["ready"]:
            post_issues(reviewed["issues"], extra_labels=ctx.extra_labels, dry_run=dry_run)
            action = "would post" if dry_run else "posted"
            log.info("[scan] %s: %s %s issue(s)", label, action, len(reviewed["issues"]))
            return True
        ctx.last_review_feedback = reviewed["feedback"]
        log.info("[scan] round %s: needs revision — %s", round_n + 1, reviewed["feedback"])
        drafted = step(
            ctx,
            f"redraft-{round_n + 1}",
            "prompts/scan/draft.md",
            json.dumps(reviewed),
        )
    ctx.last_draft = drafted
    return False


def _build_escalation_body(
    project_id: str,
    scan_type: str,
    max_rounds: int,
    last_draft: dict,
    last_review_feedback: str,
) -> str:
    """Build the markdown body for a scan-escalation issue."""
    draft_json = json.dumps(last_draft, indent=2)
    lines = [
        f"## Scan `{project_id}/{scan_type}` did not converge",
        "",
        f"The review/redraft loop ran **{max_rounds}** round(s) without the reviewer approving.",
        "",
        "### Last reviewer feedback",
        "",
        last_review_feedback or "_(no feedback captured)_",
        "",
        "### Last draft",
        "",
        "<details>",
        "<summary>Expand draft JSON</summary>",
        "",
        "```json",
        draft_json,
        "```",
        "",
        "</details>",
        "",
        "### What to do next",
        "",
        "- Review the draft and feedback to decide whether the findings are worth posting manually",
        "- Check whether the scan or review prompts need tuning",
        "- Close this issue once addressed",
    ]
    return "\n".join(lines)


def _post_escalation_issue(
    project_id: str,
    scan_type: str,
    max_rounds: int,
    ctx: _RunCtx,
    *,
    dry_run: bool,
) -> None:
    """Open (or dry-run log) a GitHub issue for a scan that failed to converge."""
    title = f"Escalation: {project_id}/{scan_type} scan did not converge"
    body = _build_escalation_body(
        project_id, scan_type, max_rounds, ctx.last_draft, ctx.last_review_feedback
    )
    labels = ["agent-scan-stalled", "autonomous"]
    if dry_run:
        log.info("\n[dry-run] would post escalation issue:")
        log.info("  title: %s", title)
        log.info("  labels: %s", labels)
        log.info("  body:\n%s\n", body)
    else:
        create_issue(title, body, labels)


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
    run_scan_preflight(project, scan)
    context = scan_context(project, scan)
    if scan_type in ("agency/history/scans", "agency/history/fixes"):
        summaries = recent_run_summaries()
        context = f"{context}\n\n## Recent run summaries\n\n{json.dumps(summaries, indent=2)}"

    run_dir = make_run_dir(f"{project_id}-{scan_type.replace('/', '-')}")
    ctx = _RunCtx(run_dir=run_dir, steps=[], refs=[], extra_labels=_issue_labels(scan_type))
    started_at = time.monotonic()

    try:
        log.info("[scan] %s/%s: finding problems...", project_id, scan_type)
        raw = step(ctx, "find", _find_prompt(scan_type), context, _FIND_CFG)

        if not raw.get("findings"):
            log.info("[scan] %s/%s: nothing to report", project_id, scan_type)
            ctx.converged = True
            return

        log.info("[scan] %s finding(s) — triaging...", len(raw["findings"]))
        clustered = step(ctx, "triage", "prompts/scan/triage.md", json.dumps(raw))

        if not clustered.get("clusters"):
            log.info("[scan] %s/%s: no actionable clusters after triage", project_id, scan_type)
            ctx.converged = True
            return

        log.info("[scan] %s cluster(s) — drafting issues...", len(clustered["clusters"]))
        drafted = step(ctx, "draft", "prompts/scan/draft.md", json.dumps(clustered))

        ctx.converged = _run_review_rounds(
            ctx, drafted, max_rounds, f"{project_id}/{scan_type}", dry_run=dry_run
        )
        if not ctx.converged:
            log.error(
                "[escalate] %s/%s: issues did not converge after %s rounds",
                project_id,
                scan_type,
                max_rounds,
            )
            _post_escalation_issue(project_id, scan_type, max_rounds, ctx, dry_run=dry_run)
            ctx.exit_code = 1

    finally:
        if not ctx.converged:
            ctx.exit_code = max(ctx.exit_code, 1)
        metadata = {
            "run_type": "scan",
            "project_id": project_id,
            "scan_type": scan_type,
            "dry_run": dry_run,
            "duration_seconds": round(time.monotonic() - started_at, 1),
            "steps": ctx.steps,
            "converged": ctx.converged,
            "exit_code": ctx.exit_code,
        }
        write_step(run_dir, "metadata", metadata)
        write_step(run_dir, "reflections", ctx.refs)
        if ctx.exit_code != 0 and sys.exc_info()[0] is None:
            sys.exit(ctx.exit_code)
