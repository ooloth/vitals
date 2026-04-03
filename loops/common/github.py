import json
import subprocess


def gh(*args: str, capture: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], capture_output=capture, text=True, check=check)


def next_open_issue() -> int | None:
    result = gh("issue", "list", "--label", "agent", "--json", "number", "--limit", "1")
    issues = json.loads(result.stdout)
    return issues[0]["number"] if issues else None


def issue_context(issue_number: int) -> str:
    return gh("issue", "view", str(issue_number), "--json", "number,title,body,labels").stdout


def open_issue_titles() -> set[str]:
    result = gh("issue", "list", "--label", "agent", "--json", "title", "--limit", "100")
    return {i["title"] for i in json.loads(result.stdout)}


def post_issues(issues: list[dict], dry_run: bool = False) -> None:
    existing = set() if dry_run else open_issue_titles()
    for issue in issues:
        title = issue["title"]
        if title in existing:
            print(f"[scan] skipping duplicate: {title!r}")
            continue
        if dry_run:
            print(f"\n[dry-run] would post issue:")
            print(f"  title: {title}")
            print(f"  label: {issue.get('label', 'sev:medium')}")
            print(f"  body:\n{issue['body']}\n")
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


def open_pr(branch: str, impl: dict, project_path) -> None:
    from loops.common.git import git

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
