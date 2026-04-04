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
        label = issue.get("label", "sev:medium")
        if dry_run:
            log.info("\n[dry-run] would post issue:")
            log.info("  title: %s", title)
            log.info("  label: %s", label)
            log.info("  body:\n%s\n", issue["body"])
        else:
            create_issue(title, issue["body"], [label])


def open_reflection_issues() -> list[dict]:
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


def comment_on_issue(issue_number: int, body: str) -> None:
    """Post a comment on an existing GitHub issue."""
    gh("issue", "comment", str(issue_number), "--body", body, capture=False)


def ensure_label(name: str, color: str = "0075ca", description: str = "") -> None:
    """Create the label if it doesn't already exist in the repo."""
    result = gh("label", "list", "--json", "name")
    existing = {label["name"] for label in json.loads(result.stdout)}
    if name not in existing:
        args = ["label", "create", name, "--color", color]
        if description:
            args += ["--description", description]
        gh(*args, capture=False)


def create_issue(title: str, body: str, labels: list[str]) -> None:
    """Ensure all labels exist, then create a GitHub issue with them."""
    for label in labels:
        ensure_label(label)
    gh(
        "issue",
        "create",
        "--title",
        title,
        "--body",
        body,
        "--label",
        ",".join(labels),
        capture=False,
    )


def add_label(issue_number: int, label: str) -> None:
    """Ensure the label exists, then apply it to an existing issue."""
    ensure_label(label)
    gh("issue", "edit", str(issue_number), "--add-label", label, capture=False)


def post_reflection_findings(findings: list[dict]) -> None:
    """Open new issues or comment on existing ones from retrospective findings."""
    for finding in findings:
        if finding.get("action") == "comment":
            comment_on_issue(finding["issue_number"], finding["body"])
        else:
            create_issue(
                finding["title"],
                finding["body"],
                finding.get("labels", ["agent-reflection"]),
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
