"""Tests for the fix loop's label and failure-comment behaviour."""

import contextlib
from unittest.mock import MagicMock, patch

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

    agent_mock = MagicMock(side_effect=agent_side_effect)
    mocks["agent"] = agent_mock
    patches["agent"] = agent_mock

    return {"patches": patches, "mocks": mocks}


def test_label_stays_on_convergence() -> None:
    """When the loop converges (PR opened), the label is NOT removed."""
    setup = _make_fix_mocks(converge=True)

    with patch.multiple("loops.fix", **setup["patches"]):
        run_fix(issue_number=7, max_rounds=1)

    setup["mocks"]["add_label"].assert_called_once_with(7, "agent-fix-in-progress")
    setup["mocks"]["remove_label"].assert_not_called()
    setup["mocks"]["comment_on_issue"].assert_not_called()
    setup["mocks"]["open_pr"].assert_called_once()


def test_non_convergence_posts_comment_and_stalls() -> None:
    """When the loop does NOT converge, a failure comment is posted and the issue is stalled."""
    setup = _make_fix_mocks(converge=False)

    with patch.multiple("loops.fix", **setup["patches"]), contextlib.suppress(SystemExit):
        run_fix(issue_number=7, max_rounds=1)

    setup["mocks"]["remove_label"].assert_called_once_with(7, "agent-fix-in-progress")
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

    with patch.multiple("loops.fix", **setup["patches"]), contextlib.suppress(SystemExit):
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
