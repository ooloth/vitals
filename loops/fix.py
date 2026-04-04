"""Agentic fix loop: pick an open issue, implement a fix, review, and open a PR."""

import dataclasses
import json
import sys
import time
from pathlib import Path

from loops.common import (
    ROOT,
    agent,
    commit_if_dirty,
    get_diff,
    git,
    issue_context,
    load_project,
    log,
    make_run_dir,
    next_open_issue,
    open_pr,
    prepare_branch,
    project_context,
    run_command,
    run_retrospective,
    run_tests,
    write_step,
)

IMPLEMENT_TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
REVIEW_TOOLS = ["Read", "Glob", "Grep"]


def _with_project_ctx(data: dict, ctx: str) -> str:
    """Serialise data as JSON, prepending project context if present."""
    payload = json.dumps(data)
    return f"{ctx}\n\n{payload}" if ctx else payload


@dataclasses.dataclass
class _RunCtx:
    run_dir: Path
    steps: list[dict]
    refs: list[dict]


def _step(
    ctx: _RunCtx,
    name: str,
    prompt: str,
    content: str,
    allowed_tools: list[str] | None = None,
) -> dict:
    """Run one agent step: time it, persist output, collect reflections."""
    t0 = time.monotonic()
    out = agent(prompt, content, allowed_tools=allowed_tools)
    ctx.steps.append({"name": name, "duration_seconds": round(time.monotonic() - t0, 1)})
    write_step(ctx.run_dir, name, out)
    ctx.refs.extend({"step": name, "text": r} for r in out.get("reflections", []))
    return out


def run_fix(
    issue_number: int | None = None, project_id: str | None = None, max_rounds: int = 10
) -> None:
    """Pick an open issue, run implement→review rounds until approved, then open a PR."""
    project = load_project(project_id) if project_id else {}
    project_path = Path(project["path"]) if project else ROOT

    original_branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=project_path).stdout.strip()

    if issue_number is None:
        issue_number = next_open_issue()
    if issue_number is None:
        log.info("[fix] no open issues to fix")
        return

    log.info("[fix] issue #%s in %s", issue_number, project_path)

    run_dir = make_run_dir(f"fix-{issue_number}")
    ctx = _RunCtx(run_dir=run_dir, steps=[], refs=[])
    started_at = time.monotonic()
    converged = False
    exit_code = 0

    for key, label in [
        ("install", "installing dependencies"),
        ("checks", "running checks"),
        ("tests", "running tests"),
    ]:
        if cmd := project.get(key):
            run_command(cmd, project_path, label)

    try:
        branch = prepare_branch(issue_number, project_path)
        proj_ctx = project_context(project)
        issue = _with_project_ctx(
            {"issue": json.loads(issue_context(issue_number)), "branch": branch},
            proj_ctx,
        )

        for round_n in range(max_rounds):
            log.info("[fix] round %s: implementing...", round_n + 1)
            impl = _step(
                ctx,
                f"implement-{round_n + 1}",
                "prompts/fix/implement.md",
                issue,
                IMPLEMENT_TOOLS,
            )

            commit_if_dirty(impl.get("pr_title", f"fix: issue #{issue_number}"), project_path)

            diff = get_diff(branch, project_path)
            if not diff or diff.startswith("(no diff"):
                log.info(
                    "[fix] round %s: no diff on %r — treating as revision needed",
                    round_n + 1,
                    branch,
                )
                issue = _with_project_ctx(
                    {
                        "issue": json.loads(issue_context(issue_number)),
                        "branch": branch,
                        "feedback": (
                            f"Branch {branch!r} has no diff against the base branch."
                            " You must make changes and ensure they are committed."
                        ),
                    },
                    proj_ctx,
                )
                continue

            tests = run_tests(project_path, project.get("tests"))

            review_context = _with_project_ctx(
                {
                    "issue": json.loads(issue_context(issue_number)),
                    "implementation": impl,
                    "diff": diff,
                    "tests": tests,
                },
                proj_ctx,
            )

            log.info("[fix] round %s: reviewing...", round_n + 1)
            reviewed = _step(
                ctx,
                f"review-{round_n + 1}",
                "prompts/fix/review.md",
                review_context,
                REVIEW_TOOLS,
            )

            if reviewed["approved"]:
                open_pr(branch, impl, project_path)
                log.info("[fix] issue #%s: PR opened (%s)", issue_number, impl["pr_title"])
                converged = True
                return

            log.info("[fix] round %s: revision needed — %s", round_n + 1, reviewed["feedback"])
            issue = _with_project_ctx(
                {
                    "issue": json.loads(issue_context(issue_number)),
                    "branch": branch,
                    "feedback": reviewed["feedback"],
                },
                proj_ctx,
            )

        log.error(
            "[escalate] issue #%s: did not converge after %s rounds", issue_number, max_rounds
        )
        exit_code = 1

    finally:
        git("checkout", original_branch, cwd=project_path)
        metadata = {
            "run_type": "fix",
            "project_id": project_id,
            "issue_number": issue_number,
            "duration_seconds": round(time.monotonic() - started_at, 1),
            "steps": ctx.steps,
            "converged": converged,
            "exit_code": exit_code,
        }
        run_retrospective(run_dir, ctx.refs, metadata)
        if exit_code != 0:
            sys.exit(exit_code)
