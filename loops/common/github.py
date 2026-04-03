"""GitHub CLI subprocess wrapper and issue/PR helpers."""

import json
import os
import shlex
import subprocess
from pathlib import Path

from loops.common.git import git
from loops.common.logging import log


def gh(*args: str, capture: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """Run a gh CLI command with the given arguments."""
    env = {**os.environ, "_GH_ARGS": shlex.join(args)}
    return subprocess.run(
        ["/bin/sh", "-c", "eval gh $_GH_ARGS"],
        capture_output=capture,
        text=True,
        check=check,
        env=env,
    )


def next_open_issue() -> int | None:
    """Return the number of the oldest open agent-labelled issue, or None."""
    result = gh("issue", "list", "--label", "agent", "--json", "number", "--limit", "1")
    issues = json.loads(result.stdout)
    return issues[0]["number"] if issues else None


def issue_context(issue_number: int) -> str:
    """Return JSON describing the given issue (number, title, body, labels)."""
    return gh("issue", "view", str(issue_number), "--json", "number,title,body,labels").stdout


def open_issue_titles() -> set[str]:
    """Return the titles of all open agent-labelled issues."""
    result = gh("issue", "list", "--label", "agent", "--json", "title", "--limit", "100")
    return {i["title"] for i in json.loads(result.stdout)}


def post_issues(issues: list[dict], *, dry_run: bool = False) -> None:
    """Post each issue to GitHub, skipping duplicates and logging dry-run output."""
    existing = set() if dry_run else open_issue_titles()
    for issue in issues:
        title = issue["title"]
        if title in existing:
            log.info("[scan] skipping duplicate: %r", title)
            continue
        if dry_run:
            log.info("\n[dry-run] would post issue:")
            log.info("  title: %s", title)
            log.info("  label: %s", issue.get("label", "sev:medium"))
            log.info("  body:\n%s\n", issue["body"])
        else:
            gh(
                "issue",
                "create",
                "--title",
                title,
                "--body",
                issue["body"],
                "--label",
                issue.get("label", "sev:medium"),
                capture=False,
            )


def open_pr(branch: str, impl: dict, project_path: Path) -> None:
    """Push the branch and open a pull request for the given implementation."""
    git("push", "-u", "origin", branch, cwd=project_path, capture=False)
    gh(
        "pr",
        "create",
        "--title",
        impl["pr_title"],
        "--body",
        impl["pr_body"],
        "--head",
        branch,
        capture=False,
    )
