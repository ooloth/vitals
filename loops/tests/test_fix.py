"""Tests for the fix loop's label and failure-comment behaviour."""

import contextlib
from pathlib import Path
from unittest.mock import MagicMock, patch

from loops.common.errors import AgentError, CommandError, GitError
from loops.common.github import next_open_issue, remove_label
from loops.fix import run_fix


def test_remove_label_calls_gh_remove_label() -> None:
    with patch("loops.common.github.gh") as mock_gh:
        remove_label(42, "agent-fix-in-progress")
    mock_gh.assert_called_once_with(
        "issue", "edit", "42", "--remove-label", "agent-fix-in-progress", capture=False
    )


def test_next_open_issue_excludes_stalled() -> None:
    """next_open_issue passes a search filter that excludes both in-progress and stalled issues."""
    with patch("loops.common.github.gh") as mock_gh:
        mock_gh.return_value = MagicMock(stdout="[]")
        next_open_issue()
    args = mock_gh.call_args[0]
    search_idx = list(args).index("--search")
    search_value = args[search_idx + 1]
    assert "-label:agent-fix-in-progress" in search_value
    assert "-label:agent-fix-stalled" in search_value


def _make_fix_mocks(*, converge: bool, no_diff: bool = False) -> dict:
    """Build a dict of mocks suitable for patching run_fix dependencies.

    When converge=True the review step approves on round 1; when False
    the loop exhausts max_rounds=1 without approval. When no_diff=True
    get_diff always returns empty so the review step is never reached.
    """
    issue_json = '{"number": 7, "title": "t", "body": "b", "labels": []}'
    review = {"approved": converge, "feedback": "nope", "reflections": []}
    impl = {"pr_title": "fix: #7", "pr_body": "body", "reflections": []}

    mocks: dict[str, MagicMock] = {}
    targets = {
        "load_project": lambda _pid: {},
        "git": MagicMock(return_value=MagicMock(stdout="main\n")),
        "next_open_issue": lambda: 7,
        "add_label": MagicMock(),
        "remove_label": MagicMock(),
        "comment_on_issue": MagicMock(),
        "make_run_dir": lambda _name: MagicMock(),
        "prepare_branch": lambda _n, _p: "fix/7",
        "project_context": lambda _p: "",
        "issue_context": lambda _n: issue_json,
        "commit_if_dirty": MagicMock(),
        "get_diff": (lambda _b, _p: "") if no_diff else (lambda _b, _p: "diff content"),
        "run_tests": lambda _p, _t: "ok",
        "open_pr": MagicMock(),
        "write_step": MagicMock(),
        "run_command": MagicMock(),
        "run_fix_preflight": MagicMock(),
    }

    patches = {}
    for name, side_effect in targets.items():
        m = (
            MagicMock(side_effect=side_effect)
            if callable(side_effect) and not isinstance(side_effect, MagicMock)
            else side_effect
        )
        mocks[name] = m
        patches[name] = m

    # agent needs to return impl on first call, review on second
    call_count = {"n": 0}

    def agent_side_effect(*_args: object, **_kwargs: object) -> dict:
        call_count["n"] += 1
        return impl if call_count["n"] % 2 == 1 else review

    mocks["agent"] = MagicMock(side_effect=agent_side_effect)

    return {"patches": patches, "mocks": mocks}


def test_label_stays_on_convergence() -> None:
    """When the loop converges (PR opened), the label is NOT removed."""
    setup = _make_fix_mocks(converge=True)

    with (
        patch.multiple("loops.fix", **setup["patches"]),
        patch("loops.common.step.agent", setup["mocks"]["agent"]),
    ):
        run_fix(issue_number=7, max_rounds=1)

    setup["mocks"]["add_label"].assert_called_once_with(7, "agent-fix-in-progress")
    setup["mocks"]["remove_label"].assert_not_called()
    setup["mocks"]["comment_on_issue"].assert_not_called()
    setup["mocks"]["open_pr"].assert_called_once()


def test_non_convergence_posts_comment_and_stalls() -> None:
    """When the loop does NOT converge, a failure comment is posted and the issue is stalled."""
    setup = _make_fix_mocks(converge=False)

    with (
        patch.multiple("loops.fix", **setup["patches"]),
        patch("loops.common.step.agent", setup["mocks"]["agent"]),
        contextlib.suppress(SystemExit),
    ):
        run_fix(issue_number=7, max_rounds=1)

    remove_calls = setup["mocks"]["remove_label"].call_args_list
    assert (7, "agent-fix-in-progress") in [c.args for c in remove_calls]
    assert (7, "ready-for-agent") in [c.args for c in remove_calls]
    setup["mocks"]["open_pr"].assert_not_called()

    # Failure comment includes round count and reviewer feedback
    comment_call = setup["mocks"]["comment_on_issue"].call_args
    assert comment_call[0][0] == 7
    comment_body = comment_call[0][1]
    assert "1/1" in comment_body
    assert "nope" in comment_body
    assert "agent-fix-stalled" in comment_body

    # Stalled label is added (second add_label call after agent-fix-in-progress)
    add_calls = setup["mocks"]["add_label"].call_args_list
    assert (7, "agent-fix-in-progress") in [c.args for c in add_calls]
    assert (7, "agent-fix-stalled") in [c.args for c in add_calls]


def test_no_diff_escalates_immediately() -> None:
    """When implement produces no diff, the agent's output is posted and the issue is stalled."""
    setup = _make_fix_mocks(converge=False, no_diff=True)

    with (
        patch.multiple("loops.fix", **setup["patches"]),
        patch("loops.common.step.agent", setup["mocks"]["agent"]),
        contextlib.suppress(SystemExit),
    ):
        run_fix(issue_number=7, max_rounds=2)

    # Only one implement call — no retry, no review
    assert setup["mocks"]["agent"].call_count == 1

    setup["mocks"]["open_pr"].assert_not_called()

    # Posts a comment containing the agent's output, not the generic failure message
    comment_call = setup["mocks"]["comment_on_issue"].call_args
    comment_body = comment_call[0][1]
    assert "no code changes" in comment_body
    assert "pr_title" in comment_body  # agent output is included

    # ready-for-agent removed (escalation) + agent-fix-in-progress removed (finally)
    remove_calls = setup["mocks"]["remove_label"].call_args_list
    assert (7, "ready-for-agent") in [c.args for c in remove_calls]
    assert (7, "agent-fix-in-progress") in [c.args for c in remove_calls]

    # agent-fix-stalled added to signal the attempt
    add_calls = setup["mocks"]["add_label"].call_args_list
    assert (7, "agent-fix-stalled") in [c.args for c in add_calls]


def _make_error_mocks(*, error_source: str) -> dict:
    """Build mocks that inject a specific error into the fix loop.

    error_source="agent" → AgentError from the first step() call.
    error_source="git"   → GitError from prepare_branch.
    """
    issue_json = '{"number": 7, "title": "t", "body": "b", "labels": []}'

    targets: dict = {
        "load_project": lambda _pid: {},
        "git": MagicMock(return_value=MagicMock(stdout="main\n")),
        "next_open_issue": lambda: 7,
        "add_label": MagicMock(),
        "remove_label": MagicMock(),
        "comment_on_issue": MagicMock(),
        "make_run_dir": lambda _name: MagicMock(),
        "project_context": lambda _p: "",
        "issue_context": lambda _n: issue_json,
        "commit_if_dirty": MagicMock(),
        "get_diff": lambda _b, _p: "diff content",
        "run_tests": lambda _p, _t: "ok",
        "open_pr": MagicMock(),
        "write_step": MagicMock(),
        "run_command": MagicMock(),
        "run_fix_preflight": MagicMock(),
    }

    if error_source == "git":
        targets["prepare_branch"] = MagicMock(
            side_effect=GitError("Working tree is dirty", path=Path("/repo")),
        )
    else:
        targets["prepare_branch"] = lambda _n, _p: "fix/7"

    mocks: dict[str, MagicMock] = {}
    patches = {}
    for name, side_effect in targets.items():
        m = (
            MagicMock(side_effect=side_effect)
            if callable(side_effect) and not isinstance(side_effect, MagicMock)
            else side_effect
        )
        mocks[name] = m
        patches[name] = m

    if error_source == "agent":
        mocks["agent"] = MagicMock(
            side_effect=AgentError("crashed", step="implement-1", exit_code=1),
        )
    else:
        mocks["agent"] = MagicMock(return_value={"reflections": []})

    return {"patches": patches, "mocks": mocks}


def test_agent_error_posts_specific_comment() -> None:
    """An AgentError during rounds posts a comment naming the step and exit code."""
    setup = _make_error_mocks(error_source="agent")

    with (
        patch.multiple("loops.fix", **setup["patches"]),
        patch("loops.common.step.agent", setup["mocks"]["agent"]),
        contextlib.suppress(SystemExit),
    ):
        run_fix(issue_number=7, max_rounds=1)

    comment_call = setup["mocks"]["comment_on_issue"].call_args
    comment_body = comment_call[0][1]
    assert "Agent error" in comment_body
    assert "implement-1" in comment_body
    assert "1" in comment_body  # exit code

    add_calls = setup["mocks"]["add_label"].call_args_list
    assert (7, "agent-fix-stalled") in [c.args for c in add_calls]


def test_git_error_posts_specific_comment() -> None:
    """A GitError from prepare_branch posts a comment mentioning the git error."""
    setup = _make_error_mocks(error_source="git")

    with (
        patch.multiple("loops.fix", **setup["patches"]),
        patch("loops.common.step.agent", setup["mocks"]["agent"]),
        contextlib.suppress(SystemExit),
    ):
        run_fix(issue_number=7, max_rounds=1)

    comment_call = setup["mocks"]["comment_on_issue"].call_args
    comment_body = comment_call[0][1]
    assert "Git error" in comment_body
    assert "dirty" in comment_body

    # Stalled even at round 0 because there's a specific error
    add_calls = setup["mocks"]["add_label"].call_args_list
    assert (7, "agent-fix-stalled") in [c.args for c in add_calls]

    # in-progress removed
    remove_calls = setup["mocks"]["remove_label"].call_args_list
    assert (7, "agent-fix-in-progress") in [c.args for c in remove_calls]


def test_setup_failure_posts_targeted_comment() -> None:
    """A CommandError from setup posts a setup-specific comment, not removing ready-for-agent."""
    setup = _make_error_mocks(error_source="agent")  # base mocks; we override below
    # Project must have a setup command so _run_setup_commands calls run_command
    setup["patches"]["load_project"] = MagicMock(
        side_effect=lambda _pid: {"path": "/repo", "check": "uv run ruff check"},
    )
    setup["mocks"]["load_project"] = setup["patches"]["load_project"]
    setup["patches"]["run_command"] = MagicMock(
        side_effect=CommandError(
            "running checks failed (exit 1): uv run ruff check",
            cmd="uv run ruff check",
            exit_code=1,
        ),
    )
    setup["mocks"]["run_command"] = setup["patches"]["run_command"]

    with (
        patch.multiple("loops.fix", **setup["patches"]),
        patch("loops.common.step.agent", setup["mocks"]["agent"]),
        contextlib.suppress(SystemExit),
    ):
        run_fix(issue_number=7, project_id="test-project", max_rounds=1)

    # Setup-specific comment posted
    comment_call = setup["mocks"]["comment_on_issue"].call_args
    comment_body = comment_call[0][1]
    assert "Setup command failed" in comment_body
    assert "uv run ruff check" in comment_body
    assert "1" in comment_body  # exit code

    # in-progress removed, stalled added
    add_calls = setup["mocks"]["add_label"].call_args_list
    assert (7, "agent-fix-stalled") in [c.args for c in add_calls]
    remove_calls = setup["mocks"]["remove_label"].call_args_list
    assert (7, "agent-fix-in-progress") in [c.args for c in remove_calls]

    # ready-for-agent NOT removed (the issue is fine, the environment isn't)
    assert (7, "ready-for-agent") not in [c.args for c in remove_calls]

    # Agent was never called (setup failed before rounds)
    setup["mocks"]["agent"].assert_not_called()
