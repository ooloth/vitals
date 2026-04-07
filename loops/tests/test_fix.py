"""Tests for the fix loop's issue-claiming label behaviour."""

import contextlib
from unittest.mock import MagicMock, patch

from loops.common.github import remove_label
from loops.fix import run_fix


def test_remove_label_calls_gh_remove_label() -> None:
    with patch("loops.common.github.gh") as mock_gh:
        remove_label(42, "agent-fix-in-progress")
    mock_gh.assert_called_once_with(
        "issue", "edit", "42", "--remove-label", "agent-fix-in-progress", capture=False
    )


def _make_fix_mocks(*, converge: bool) -> dict:
    """Build a dict of mocks suitable for patching run_fix dependencies.

    When converge=True the review step approves on round 1; when False
    the loop exhausts max_rounds=1 without approval.
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
        "make_run_dir": lambda _name: MagicMock(),
        "prepare_branch": lambda _n, _p: "fix/7",
        "project_context": lambda _p: "",
        "issue_context": lambda _n: issue_json,
        "commit_if_dirty": MagicMock(),
        "get_diff": lambda _b, _p: "diff content",
        "run_tests": lambda _p, _t: "ok",
        "open_pr": MagicMock(),
        "write_step": MagicMock(),
        "run_command": MagicMock(),
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
    setup["mocks"]["open_pr"].assert_called_once()


def test_label_removed_on_non_convergence() -> None:
    """When the loop does NOT converge, the label IS removed."""
    setup = _make_fix_mocks(converge=False)

    with patch.multiple("loops.fix", **setup["patches"]), contextlib.suppress(SystemExit):
        run_fix(issue_number=7, max_rounds=1)

    setup["mocks"]["add_label"].assert_called_once_with(7, "agent-fix-in-progress")
    setup["mocks"]["remove_label"].assert_called_once_with(7, "agent-fix-in-progress")
    setup["mocks"]["open_pr"].assert_not_called()
