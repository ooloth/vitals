import json
import sys
from pathlib import Path

from loops.common import (
    ROOT,
    agent,
    commit_if_dirty,
    get_diff,
    git,
    issue_context,
    load_project,
    next_open_issue,
    open_pr,
    prepare_branch,
    run_command,
    run_tests,
)

IMPLEMENT_TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
REVIEW_TOOLS = ["Read", "Glob", "Grep"]


def run_fix(
    issue_number: int | None = None, project_id: str | None = None, max_rounds: int = 10
) -> None:
    project = load_project(project_id) if project_id else {}
    project_path = Path(project["path"]) if project else ROOT

    original_branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=project_path).stdout.strip()

    if issue_number is None:
        issue_number = next_open_issue()
    if issue_number is None:
        print("[fix] no open issues to fix")
        return

    print(f"[fix] issue #{issue_number} in {project_path}", flush=True)

    for key, label in [
        ("install", "installing dependencies"),
        ("checks", "running checks"),
        ("tests", "running tests"),
    ]:
        if cmd := project.get(key):
            run_command(cmd, project_path, label)

    try:
        branch = prepare_branch(issue_number, project_path)
        issue = json.dumps(
            {
                "issue": json.loads(issue_context(issue_number)),
                "branch": branch,
            }
        )

        for round_n in range(max_rounds):
            print(f"[fix] round {round_n + 1}: implementing...", flush=True)
            impl = agent("prompts/fix/implement.md", issue, allowed_tools=IMPLEMENT_TOOLS)

            commit_if_dirty(impl.get("pr_title", f"fix: issue #{issue_number}"), project_path)

            diff = get_diff(branch, project_path)
            if not diff or diff.startswith("(no diff"):
                print(
                    f"[fix] round {round_n + 1}: no diff on {branch!r} — treating as revision needed",
                    flush=True,
                )
                issue = json.dumps(
                    {
                        "issue": json.loads(issue_context(issue_number)),
                        "branch": branch,
                        "feedback": f"Branch {branch!r} has no diff against the base branch. You must make changes and ensure they are committed.",
                    }
                )
                continue

            tests = run_tests(project_path, project.get("tests"))

            review_context = json.dumps(
                {
                    "issue": json.loads(issue_context(issue_number)),
                    "implementation": impl,
                    "diff": diff,
                    "tests": tests,
                }
            )

            print(f"[fix] round {round_n + 1}: reviewing...", flush=True)
            reviewed = agent("prompts/fix/review.md", review_context, allowed_tools=REVIEW_TOOLS)

            if reviewed["approved"]:
                open_pr(branch, impl, project_path)
                print(f"[fix] issue #{issue_number}: PR opened ({impl['pr_title']})")
                return

            print(
                f"[fix] round {round_n + 1}: revision needed — {reviewed['feedback']}", flush=True
            )
            issue = json.dumps(
                {
                    "issue": json.loads(issue_context(issue_number)),
                    "branch": branch,
                    "feedback": reviewed["feedback"],
                }
            )

        print(
            f"[escalate] issue #{issue_number}: did not converge after {max_rounds} rounds",
            file=sys.stderr,
        )
        sys.exit(1)

    finally:
        git("checkout", original_branch, cwd=project_path)
