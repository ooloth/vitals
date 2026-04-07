"""General-purpose GitHub CLI primitives: gh wrapper, issue/label/PR helpers.

Belongs here: thin wrappers around gh commands usable by any loop or
module (gh, create_issue, add_label, ensure_label, comment_on_issue,
open_pr, issue_context, open_autonomous_issues, open_autonomous_titles,
approved_issue_count, next_open_issue, post_issues, edit_issue_body,
close_issue).

Does not belong here: domain logic tied to a specific loop or agent
(e.g. retrospective findings, reflection issue queries).
"""

import functools
import json
import shutil
import subprocess
import time
from pathlib import Path

from loops.common.git import git
from loops.common.logging import log

MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 1


@functools.cache
def _gh_path() -> str:
    """Return the absolute path to the gh CLI, raising if not installed."""
    path = shutil.which("gh")
    if not path:
        msg = "gh CLI not found in PATH"
        raise RuntimeError(msg)
    return path


def gh(*args: str, capture: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """Run a gh CLI command, retrying transient failures with exponential backoff.

    When check=True, transient CalledProcessError failures are retried up to
    MAX_RETRIES times with exponential backoff. When check=False, no retry is
    attempted (the caller handles errors).
    """
    cmd = [_gh_path(), *args]
    if not check:
        # S603: sole allowed suppression — see module docstring.
        return subprocess.run(cmd, capture_output=capture, text=True, check=False)  # noqa: S603

    last_err: subprocess.CalledProcessError | None = None
    for attempt in range(1, MAX_RETRIES + 2):  # attempts 1 … MAX_RETRIES+1
        try:
            # S603: sole allowed suppression — see module docstring.
            return subprocess.run(cmd, capture_output=capture, text=True, check=True)  # noqa: S603
        except subprocess.CalledProcessError as exc:
            last_err = exc
            if attempt <= MAX_RETRIES:
                delay = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
                cmd_str = " ".join(args)
                log.warning(
                    "[gh] `gh %s` failed (attempt %s/%s), retrying in %ss…",
                    cmd_str,
                    attempt,
                    MAX_RETRIES + 1,
                    delay,
                )
                time.sleep(delay)

    cmd_str = " ".join(args)
    msg = f"`gh {cmd_str}` failed after {MAX_RETRIES + 1} attempts"
    raise subprocess.SubprocessError(msg) from last_err


def next_open_issue() -> int | None:
    """Return the number of the oldest open ready-for-agent issue not already claimed or stalled."""
    result = gh(
        "issue",
        "list",
        "--label",
        "ready-for-agent",
        "--search",
        "-label:agent-fix-in-progress -label:agent-fix-stalled",
        "--json",
        "number",
        "--limit",
        "1",
    )
    issues = json.loads(result.stdout)
    return issues[0]["number"] if issues else None


def issue_context(issue_number: int) -> str:
    """Return JSON describing the given issue (number, title, body, labels)."""
    return gh("issue", "view", str(issue_number), "--json", "number,title,body,labels").stdout


def open_autonomous_issues() -> list[dict]:
    """Return full details of all open autonomously-created issues."""
    result = gh(
        "issue",
        "list",
        "--label",
        "autonomous",
        "--json",
        "number,title,body,labels",
        "--limit",
        "100",
    )
    return json.loads(result.stdout)


def open_autonomous_titles() -> set[str]:
    """Return the titles of all open autonomously-created issues (for deduplication)."""
    result = gh("issue", "list", "--label", "autonomous", "--json", "title", "--limit", "100")
    return {i["title"] for i in json.loads(result.stdout)}


def approved_issue_count() -> int:
    """Return the number of open ready-for-agent issues (for backpressure checks)."""
    result = gh("issue", "list", "--label", "ready-for-agent", "--json", "number", "--limit", "100")
    return len(json.loads(result.stdout))


def post_issues(
    issues: list[dict], *, extra_labels: list[str] | None = None, dry_run: bool = False
) -> None:
    """Post each issue to GitHub, skipping duplicates and logging dry-run output."""
    existing = set() if dry_run else open_autonomous_titles()
    for issue in issues:
        title = issue["title"]
        if title in existing:
            log.info("[scan] skipping duplicate: %r", title)
            continue
        labels = [issue.get("label", "sev:medium"), *(extra_labels or [])]
        if dry_run:
            log.info("\n[dry-run] would post issue:")
            log.info("  title: %s", title)
            log.info("  labels: %s", labels)
            log.info("  body:\n%s\n", issue["body"])
        else:
            create_issue(title, issue["body"], labels)


def comment_on_issue(issue_number: int, body: str) -> None:
    """Post a comment on an existing GitHub issue."""
    gh("issue", "comment", str(issue_number), "--body", body, capture=False)


def edit_issue_body(issue_number: int, body: str) -> None:
    """Replace an issue's body with new content."""
    gh("issue", "edit", str(issue_number), "--body", body, capture=False)


def close_issue(issue_number: int, comment: str) -> None:
    """Close an issue with an explanatory comment."""
    comment_on_issue(issue_number, comment)
    gh("issue", "close", str(issue_number), capture=False)


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


def remove_label(issue_number: int, label: str) -> None:
    """Remove a label from an existing issue."""
    gh("issue", "edit", str(issue_number), "--remove-label", label, capture=False)


def open_pr(branch: str, impl: dict, project_path: Path) -> None:
    """Push the branch and open a pull request for the given implementation."""
    git("push", "--force-with-lease", "-u", "origin", branch, cwd=project_path, capture=False)
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
