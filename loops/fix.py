"""Agentic fix loop: pick an open issue, implement a fix, review, and open a PR."""

import dataclasses
import json
import sys
import time
from pathlib import Path

from loops.common import (
    ROOT,
    AgentConfig,
    add_label,
    agent,
    comment_on_issue,
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
    remove_label,
    run_command,
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
    project_id: str | None
    issue_number: int
    started_at: float
    steps: list[dict] = dataclasses.field(default_factory=list)
    refs: list[dict] = dataclasses.field(default_factory=list)
    rounds_completed: int = 0
    last_rejection: str = ""
    converged: bool = False
    exit_code: int = 0

    def write_metadata(self) -> None:
        """Persist run metadata and collected reflections."""
        metadata = {
            "run_type": "fix",
            "project_id": self.project_id,
            "issue_number": self.issue_number,
            "duration_seconds": round(time.monotonic() - self.started_at, 1),
            "steps": self.steps,
            "converged": self.converged,
            "exit_code": self.exit_code,
        }
        write_step(self.run_dir, "metadata", metadata)
        write_step(self.run_dir, "reflections", self.refs)


def _step(
    ctx: _RunCtx,
    name: str,
    prompt: str,
    content: str,
    allowed_tools: list[str] | None = None,
) -> dict:
    """Run one agent step: time it, persist output, collect reflections."""
    t0 = time.monotonic()
    cfg = AgentConfig(
        allowed_tools=allowed_tools,
        transcript_path=ctx.run_dir / f"{name}-transcript.jsonl",
        step_name=name,
    )
    out = agent(prompt, content, cfg)
    ctx.steps.append({"name": name, "duration_seconds": round(time.monotonic() - t0, 1)})
    write_step(ctx.run_dir, name, out)
    ctx.refs.extend({"step": name, "text": r} for r in out.get("reflections", []))
    return out


def _run_setup_commands(project: dict, project_path: Path) -> None:
    """Run install / check / test commands configured for the project."""
    for key, label in [
        ("install", "installing dependencies"),
        ("check", "running checks"),
        ("test", "running tests"),
    ]:
        if cmd := project.get(key):
            run_command(cmd, project_path, label)


def _build_failure_comment(ctx: _RunCtx, max_rounds: int) -> str:
    """Build a markdown comment describing why the fix loop did not converge."""
    lines = [
        "## 🛑 Automatic fix did not converge",
        "",
        f"The fix loop ran **{ctx.rounds_completed}/{max_rounds}** implement→review rounds"
        " without the reviewer approving.",
        "",
        "### Last rejection",
        "",
        ctx.last_rejection or "_(no reviewer feedback — all rounds produced no diff)_",
        "",
        "### What to do next",
        "",
        "- **Rewrite the issue** to be more specific or break it into smaller pieces",
        "- **Add domain context** the agent may be missing (e.g. relevant code snippets,"
        " architectural constraints)",
        "- Remove the `agent-fix-stalled` label when ready for another attempt",
    ]
    return "\n".join(lines)


def _run_rounds(
    ctx: _RunCtx,
    project: dict,
    project_path: Path,
    max_rounds: int,
) -> None:
    """Run implement→review rounds until approved or max_rounds exhausted."""
    branch = prepare_branch(ctx.issue_number, project_path)
    proj_ctx = project_context(project)
    issue = _with_project_ctx(
        {"issue": json.loads(issue_context(ctx.issue_number)), "branch": branch},
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

        commit_if_dirty(impl.get("pr_title", f"fix: issue #{ctx.issue_number}"), project_path)

        ctx.rounds_completed = round_n + 1

        diff = get_diff(branch, project_path)
        if not diff or diff.startswith("(no diff"):
            ctx.last_rejection = f"Round {round_n + 1} produced no diff against the base branch."
            log.info(
                "[fix] round %s: no diff on %r — treating as revision needed",
                round_n + 1,
                branch,
            )
            issue = _with_project_ctx(
                {
                    "issue": json.loads(issue_context(ctx.issue_number)),
                    "branch": branch,
                    "feedback": (
                        f"Branch {branch!r} has no diff against the base branch."
                        " You must make changes and ensure they are committed."
                    ),
                },
                proj_ctx,
            )
            continue

        tests = run_tests(project_path, project.get("test"))

        review_context = _with_project_ctx(
            {
                "issue": json.loads(issue_context(ctx.issue_number)),
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
            log.info("[fix] issue #%s: PR opened (%s)", ctx.issue_number, impl["pr_title"])
            ctx.converged = True
            return

        ctx.last_rejection = reviewed["feedback"]
        log.info("[fix] round %s: revision needed — %s", round_n + 1, reviewed["feedback"])
        issue = _with_project_ctx(
            {
                "issue": json.loads(issue_context(ctx.issue_number)),
                "branch": branch,
                "feedback": reviewed["feedback"],
            },
            proj_ctx,
        )

    log.error(
        "[escalate] issue #%s: did not converge after %s rounds", ctx.issue_number, max_rounds
    )
    ctx.exit_code = 1


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
    add_label(issue_number, "agent-fix-in-progress")

    run_dir = make_run_dir(f"fix-{issue_number}")
    ctx = _RunCtx(
        run_dir=run_dir,
        project_id=project_id,
        issue_number=issue_number,
        started_at=time.monotonic(),
    )

    _run_setup_commands(project, project_path)

    try:
        _run_rounds(ctx, project, project_path, max_rounds)
    finally:
        if not ctx.converged:
            ctx.exit_code = max(ctx.exit_code, 1)
            remove_label(issue_number, "agent-fix-in-progress")
            if ctx.rounds_completed > 0:
                comment_on_issue(issue_number, _build_failure_comment(ctx, max_rounds))
                add_label(issue_number, "agent-fix-stalled")
        git("checkout", original_branch, cwd=project_path)
        ctx.write_metadata()
        if ctx.exit_code != 0 and sys.exc_info()[0] is None:
            sys.exit(ctx.exit_code)
