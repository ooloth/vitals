"""Tests for the groom loop's coordinator logic."""

from unittest.mock import MagicMock, call, patch

from loops.groom import _apply_verdict, run_groom


class TestApplyVerdict:
    """_apply_verdict routes verdicts to the correct GitHub action."""

    def test_present_is_noop(self) -> None:
        with (
            patch("loops.groom.edit_issue_body") as edit,
            patch("loops.groom.close_issue") as close,
        ):
            _apply_verdict({"verdict": "present"}, 5, dry_run=False)

        edit.assert_not_called()
        close.assert_not_called()

    def test_partial_edits_body(self) -> None:
        with patch("loops.groom.edit_issue_body") as edit:
            _apply_verdict(
                {"verdict": "partial", "updated_body": "new body"},
                5,
                dry_run=False,
            )

        edit.assert_called_once_with(5, "new body")

    def test_partial_dry_run_does_not_edit(self) -> None:
        with patch("loops.groom.edit_issue_body") as edit:
            _apply_verdict(
                {"verdict": "partial", "updated_body": "new body"},
                5,
                dry_run=True,
            )

        edit.assert_not_called()

    def test_resolved_closes_with_comment(self) -> None:
        with patch("loops.groom.close_issue") as close:
            _apply_verdict(
                {"verdict": "resolved", "summary": "already fixed"},
                5,
                dry_run=False,
            )

        close.assert_called_once_with(5, "Closed by groom: already fixed")

    def test_resolved_dry_run_does_not_close(self) -> None:
        with patch("loops.groom.close_issue") as close:
            _apply_verdict(
                {"verdict": "resolved", "summary": "already fixed"},
                5,
                dry_run=True,
            )

        close.assert_not_called()

    def test_unknown_verdict_skips(self) -> None:
        with (
            patch("loops.groom.edit_issue_body") as edit,
            patch("loops.groom.close_issue") as close,
        ):
            _apply_verdict({"verdict": "banana"}, 5, dry_run=False)

        edit.assert_not_called()
        close.assert_not_called()


class TestRunGroom:
    """run_groom orchestrates evaluation of open issues."""

    def test_no_issues_returns_early(self) -> None:
        with (
            patch("loops.groom.load_project", return_value={"id": "agency", "scans": []}),
            patch("loops.groom.open_autonomous_issues", return_value=[]),
            patch("loops.common.step.agent") as agent_mock,
        ):
            run_groom("agency")

        agent_mock.assert_not_called()

    def test_evaluates_each_issue(self) -> None:
        issues = [
            {"number": 1, "title": "Issue A", "body": "...", "labels": []},
            {"number": 2, "title": "Issue B", "body": "...", "labels": []},
        ]
        verdicts = [
            {"verdict": "present", "summary": "still there", "reflections": []},
            {"verdict": "resolved", "summary": "gone", "reflections": []},
        ]

        with (
            patch("loops.groom.load_project", return_value={"id": "agency", "scans": []}),
            patch("loops.groom.open_autonomous_issues", return_value=issues),
            patch("loops.common.step.agent", side_effect=verdicts),
            patch("loops.groom._apply_verdict") as apply_mock,
            patch("loops.groom.make_run_dir", return_value=MagicMock()),
            patch("loops.groom.write_step"),
        ):
            run_groom("agency", dry_run=True)

        assert apply_mock.call_args_list == [
            call(verdicts[0], 1, dry_run=True),
            call(verdicts[1], 2, dry_run=True),
        ]
