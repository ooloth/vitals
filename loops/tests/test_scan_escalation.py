"""Tests for the scan loop's escalation behaviour on non-convergence."""

import contextlib
from typing import Any
from unittest.mock import MagicMock, patch

from loops.scan import run_scan


def _make_scan_mocks(*, converge: bool) -> dict:
    """Build mocks for patching run_scan dependencies.

    When converge=True the review step approves on round 1; when False
    the loop exhausts max_rounds=1 without approval.
    """
    findings = [{"description": "problem A", "severity": "medium"}]
    clusters = [{"title": "cluster 1", "findings": findings}]
    draft_issues = [{"title": "Fix A", "body": "details", "label": "sev:medium"}]

    find_result = {"findings": findings, "reflections": []}
    triage_result = {"clusters": clusters, "reflections": []}
    draft_result = {"issues": draft_issues, "reflections": []}
    review_result = {
        "ready": converge,
        "issues": draft_issues if converge else [],
        "feedback": "needs more detail",
        "reflections": [],
    }
    # Redraft returns a revised version of the draft (same structure as draft)
    redraft_result = {"issues": draft_issues, "reflections": []}
    # Dedup step returns "post" action for each approved issue
    dedup_result = {
        "actions": [{"action": "post", "title": "Fix A", "body": "details", "label": "sev:medium"}],
        "reflections": [],
    }

    call_count = {"n": 0}
    if converge:
        step_sequence = [find_result, triage_result, draft_result, review_result, dedup_result]
    else:
        step_sequence = [find_result, triage_result, draft_result, review_result, redraft_result]

    def agent_side_effect(*_args: object, **_kwargs: object) -> dict:
        idx = min(call_count["n"], len(step_sequence) - 1)
        call_count["n"] += 1
        return step_sequence[idx]

    project = {
        "id": "test-project",
        "path": "/var/test-project",
        "scans": [{"type": "codebase/dead-code", "paths": ["src/"]}],
    }

    mocks: dict[str, MagicMock] = {}
    targets = {
        "approved_issue_count": lambda: 0,
        "load_project": lambda _pid: project,
        "run_scan_preflight": MagicMock(),
        "scan_context": lambda _p, _s: "context",
        "make_run_dir": lambda _name: MagicMock(),
        "open_issues": list,
        "comment_on_issue": MagicMock(),
        "create_issue": MagicMock(),
        "write_step": MagicMock(),
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

    mocks["agent"] = MagicMock(side_effect=agent_side_effect)

    return {"patches": patches, "mocks": mocks}


def test_scan_convergence_posts_issues_no_escalation() -> None:
    """When review approves, issues are posted via dedup dispatch (no escalation)."""
    setup = _make_scan_mocks(converge=True)

    with (
        patch.multiple("loops.scan", **setup["patches"]),
        patch("loops.common.step.agent", setup["mocks"]["agent"]),
    ):
        run_scan("test-project", scan_type="codebase/dead-code", max_rounds=1)

    # Dedup dispatched one "post" action → create_issue called once (not an escalation)
    create_call = setup["mocks"]["create_issue"].call_args
    title, _body, labels = create_call.args
    assert title == "Fix A"
    assert "agent-scan-stalled" not in labels


def test_scan_non_convergence_posts_escalation_issue() -> None:
    """When review rounds exhaust without approval, an escalation issue is created."""
    setup = _make_scan_mocks(converge=False)

    with (
        patch.multiple("loops.scan", **setup["patches"]),
        patch("loops.common.step.agent", setup["mocks"]["agent"]),
        contextlib.suppress(SystemExit),
    ):
        run_scan("test-project", scan_type="codebase/dead-code", max_rounds=1)

    # Only call to create_issue should be the escalation
    create_call = setup["mocks"]["create_issue"].call_args
    title, body, labels = create_call.args
    assert "test-project/codebase/dead-code" in title
    assert "Escalation" in title
    assert "agent-scan-stalled" in labels
    assert "autonomous" in labels
    assert "needs more detail" in body
    assert "Fix A" in body


def test_scan_identical_redraft_escalates_early() -> None:
    """When a redraft is identical to the previous draft, escalate without running more rounds."""
    findings = [{"description": "problem A", "severity": "medium"}]
    clusters = [{"title": "cluster 1", "findings": findings}]
    draft_issues = [{"title": "Fix A", "body": "details", "label": "sev:medium"}]

    find_result = {"findings": findings, "reflections": []}
    triage_result = {"clusters": clusters, "reflections": []}
    draft_result = {"issues": draft_issues, "reflections": []}
    review_reject = {
        "ready": False,
        "issues": [],
        "feedback": "needs more detail",
        "reflections": [],
    }
    # Redraft returns identical issues — different reflections should be ignored
    redraft_identical = {"issues": draft_issues, "reflections": ["tried but couldn't improve"]}

    step_sequence = [find_result, triage_result, draft_result, review_reject, redraft_identical]
    call_count = {"n": 0}

    def agent_side_effect(*_args: object, **_kwargs: object) -> dict:
        idx = min(call_count["n"], len(step_sequence) - 1)
        call_count["n"] += 1
        return step_sequence[idx]

    project = {
        "id": "test-project",
        "path": "/var/test-project",
        "scans": [{"type": "codebase/dead-code", "paths": ["src/"]}],
    }

    patches: dict[str, Any] = {
        "approved_issue_count": MagicMock(side_effect=lambda: 0),
        "load_project": MagicMock(side_effect=lambda _pid: project),
        "run_scan_preflight": MagicMock(),
        "scan_context": MagicMock(side_effect=lambda _p, _s: "context"),
        "make_run_dir": MagicMock(return_value=MagicMock()),
        "open_issues": MagicMock(side_effect=list),
        "comment_on_issue": MagicMock(),
        "create_issue": MagicMock(),
        "write_step": MagicMock(),
    }
    mock_agent = MagicMock(side_effect=agent_side_effect)

    with (
        patch.multiple("loops.scan", **patches),
        patch("loops.common.step.agent", mock_agent),
        contextlib.suppress(SystemExit),
    ):
        # max_rounds=3 — if the identical-redraft check is missing, we'd see
        # 9 agent calls (find, triage, draft, 3x(review, redraft)); with the
        # check we see exactly 5 (find, triage, draft, review-1, redraft-1).
        run_scan("test-project", scan_type="codebase/dead-code", max_rounds=3)

    assert mock_agent.call_count == 5

    # Escalation issue was posted
    create_call = patches["create_issue"].call_args
    title, _body, labels = create_call.args
    assert "Escalation" in title
    assert "agent-scan-stalled" in labels


def test_scan_non_convergence_dry_run_skips_escalation_post() -> None:
    """In dry-run mode, escalation is logged but no issue is created."""
    setup = _make_scan_mocks(converge=False)

    with (
        patch.multiple("loops.scan", **setup["patches"]),
        patch("loops.common.step.agent", setup["mocks"]["agent"]),
        contextlib.suppress(SystemExit),
    ):
        run_scan("test-project", scan_type="codebase/dead-code", max_rounds=1, dry_run=True)

    setup["mocks"]["create_issue"].assert_not_called()
