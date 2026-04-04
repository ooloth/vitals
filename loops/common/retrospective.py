"""Retrospective agent: analyse a completed run and post findings as issues."""

import json
import sys
from pathlib import Path

from loops.common.agent import agent
from loops.common.github import comment_on_issue, create_issue, gh
from loops.common.logging import log
from loops.common.logs import recent_run_dirs, write_step


def _fetch_open_issues() -> list[dict]:
    """Return open agent-reflection issues (number, title, truncated body)."""
    result = gh(
        "issue",
        "list",
        "--label",
        "agent-reflection",
        "--json",
        "number,title,body",
        "--limit",
        "50",
    )
    issues = json.loads(result.stdout)
    return [
        {"number": i["number"], "title": i["title"], "body_excerpt": i["body"][:300]}
        for i in issues
    ]


def _post_findings(findings: list[dict], *, dry_run: bool = False) -> None:
    """Open new issues or comment on existing ones from retrospective findings."""
    for finding in findings:
        if dry_run:
            log.info(
                "[dry-run] would post retrospective finding: %s", finding.get("title", "(comment)")
            )
            continue
        if finding.get("action") == "comment":
            comment_on_issue(finding["issue_number"], finding["body"])
        else:
            create_issue(
                finding["title"],
                finding["body"],
                finding.get("labels", ["agent-reflection"]),
            )


def run_retrospective(
    run_dir: Path,
    reflections: list[dict],
    metadata: dict,
    *,
    dry_run: bool = False,
) -> None:
    """Run the retrospective agent and post any findings as GitHub issues."""
    context = json.dumps(
        {
            "run_metadata": metadata,
            "reflections": reflections,
            "recent_log_dirs": [str(d) for d in recent_run_dirs(limit=10) if d != run_dir],
            "open_reflection_issues": _fetch_open_issues(),
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
        action = "would post" if dry_run else "posting"
        log.info("[retrospective] %s %s finding(s)...", action, len(findings))
        _post_findings(findings, dry_run=dry_run)
    else:
        log.info("[retrospective] no findings to post")
