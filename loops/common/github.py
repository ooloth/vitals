"""General-purpose GitHub CLI primitives: gh wrapper, issue/label/PR helpers.

Belongs here: thin wrappers around gh commands usable by any loop or
module (gh, create_issue, add_label, ensure_label, comment_on_issue,
open_pr, issue_context, open_autonomous_titles, approved_issue_count, next_open_issue, post_issues).

Does not belong here: domain logic tied to a specific loop or agent
(e.g. retrospective findings, reflection issue queries).
"""

import functools
import json
import shutil
import subprocess
from pathlib import Path

from loops.common.git import git
from loops.common.logging import log


@functools.cache
def _gh_path() -> str:
    """Return the absolute path to the gh CLI, raising if not installed."""
    path = shutil.which("gh")
    if not path:
        msg = "gh CLI not found in PATH"
        raise RuntimeError(msg)
    return path


def gh(*args: str, capture: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """Run a gh CLI command with the given arguments."""
    # S603 fires on any subprocess.run call regardless of arguments — there is no
    # code pattern that satisfies it while still using subprocess. All args here
    # are string literals from internal call sites, never from untrusted user input.
    return subprocess.run(  # noqa: S603
        [_gh_path(), *args],
        capture_output=capture,
        text=True,
        check=check,
    )


def next_open_issue() -> int | None:
    """Return the number of the oldest open approved issue, or None."""
    result = gh("issue", "list", "--label", "approved", "--json", "number", "--limit", "1")
    issues = json.loads(result.stdout)
    return issues[0]["number"] if issues else None


def issue_context(issue_number: int) -> str:
    """Return JSON describing the given issue (number, title, body, labels)."""
    return gh("issue", "view", str(issue_number), "--json", "number,title,body,labels").stdout


def open_autonomous_titles() -> set[str]:
    """Return the titles of all open autonomously-created issues (for deduplication)."""
    result = gh("issue", "list", "--label", "autonomous", "--json", "title", "--limit", "100")
    return {i["title"] for i in json.loads(result.stdout)}


def approved_issue_count() -> int:
    """Return the number of open approved issues (for backpressure checks)."""
    result = gh("issue", "list", "--label", "approved", "--json", "number", "--limit", "100")
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
