"""Tests for pre-flight environment checks."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from loops.common.preflight import (
    _check_gh_auth,
    _check_op_on_path,
    _check_project_path,
    _check_scan_token,
    _check_secrets_env,
    run_fix_preflight,
    run_groom_preflight,
    run_scan_preflight,
)


class TestCheckGhAuth:
    def test_passes_when_authenticated(self) -> None:
        with patch("loops.common.preflight.gh", return_value=MagicMock(returncode=0)):
            assert _check_gh_auth() is None

    def test_fails_when_not_authenticated(self) -> None:
        with patch("loops.common.preflight.gh", return_value=MagicMock(returncode=1)):
            error = _check_gh_auth()

        assert error is not None
        assert "gh auth login" in error

    def test_calls_gh_with_check_false(self) -> None:
        with patch("loops.common.preflight.gh", return_value=MagicMock(returncode=0)) as mock_gh:
            _check_gh_auth()

        mock_gh.assert_called_once_with("auth", "status", check=False)


class TestCheckOpOnPath:
    def test_passes_when_op_found(self) -> None:
        with patch("loops.common.preflight.shutil.which", return_value="/usr/bin/op"):
            assert _check_op_on_path() is None

    def test_fails_when_op_missing(self) -> None:
        with patch("loops.common.preflight.shutil.which", return_value=None):
            error = _check_op_on_path()

        assert error is not None
        assert "op" in error
        assert "PATH" in error


class TestCheckSecretsEnv:
    def test_passes_when_file_exists(self, tmp_path: Path) -> None:
        with patch("loops.common.preflight.ROOT", tmp_path):
            (tmp_path / "secrets.env").touch()
            assert _check_secrets_env() is None

    def test_fails_when_file_missing(self, tmp_path: Path) -> None:
        with patch("loops.common.preflight.ROOT", tmp_path):
            error = _check_secrets_env()

        assert error is not None
        assert "secrets.env" in error


class TestCheckScanToken:
    def test_passes_when_no_token_configured(self) -> None:
        assert _check_scan_token({"type": "codebase/dead-code"}) is None

    def test_passes_when_env_var_set(self) -> None:
        with patch.dict("os.environ", {"AXIOM_TOKEN": "secret-value"}):
            assert _check_scan_token({"token": "${AXIOM_TOKEN}"}) is None

    def test_fails_when_env_var_missing(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            error = _check_scan_token({"token": "${AXIOM_TOKEN}"})

        assert error is not None
        assert "AXIOM_TOKEN" in error
        assert "op run" in error

    def test_passes_when_token_format_unrecognized(self) -> None:
        assert _check_scan_token({"token": "literal-value"}) is None


class TestCheckProjectPath:
    def test_passes_when_no_path_configured(self) -> None:
        assert _check_project_path({"id": "pilots"}) is None

    def test_passes_when_path_exists(self, tmp_path: Path) -> None:
        assert _check_project_path({"path": str(tmp_path)}) is None

    def test_fails_when_path_missing(self) -> None:
        error = _check_project_path({"path": "/nonexistent/path/to/project"})

        assert error is not None
        assert "/nonexistent/path/to/project" in error


class TestRunScanPreflight:
    def test_exits_1_when_any_check_fails(self) -> None:
        with (
            patch("loops.common.preflight._check_gh_auth", return_value="gh auth failed"),
            patch("loops.common.preflight._check_op_on_path", return_value=None),
            patch("loops.common.preflight._check_secrets_env", return_value=None),
            patch("loops.common.preflight._check_scan_token", return_value=None),
            patch("loops.common.preflight._check_project_path", return_value=None),
            pytest.raises(SystemExit, match="1"),
        ):
            run_scan_preflight({}, {})

    def test_does_not_exit_when_all_checks_pass(self) -> None:
        with (
            patch("loops.common.preflight._check_gh_auth", return_value=None),
            patch("loops.common.preflight._check_op_on_path", return_value=None),
            patch("loops.common.preflight._check_secrets_env", return_value=None),
            patch("loops.common.preflight._check_scan_token", return_value=None),
            patch("loops.common.preflight._check_project_path", return_value=None),
        ):
            run_scan_preflight({}, {})  # should not raise

    def test_collects_all_errors(self) -> None:
        with (
            patch("loops.common.preflight._check_gh_auth", return_value="error 1"),
            patch("loops.common.preflight._check_op_on_path", return_value="error 2"),
            patch("loops.common.preflight._check_secrets_env", return_value=None),
            patch("loops.common.preflight._check_scan_token", return_value="error 3"),
            patch("loops.common.preflight._check_project_path", return_value=None),
            patch("loops.common.preflight.log") as mock_log,
            pytest.raises(SystemExit),
        ):
            run_scan_preflight({}, {})

        mock_log.error.assert_any_call("[preflight] %s check(s) failed:", 3)
        error_calls = [c for c in mock_log.error.call_args_list if "✗" in str(c)]
        assert len(error_calls) == 3


class TestRunFixPreflight:
    def test_exits_1_when_gh_auth_fails(self) -> None:
        with (
            patch("loops.common.preflight._check_gh_auth", return_value="gh auth failed"),
            patch("loops.common.preflight._check_op_on_path", return_value=None),
            patch("loops.common.preflight._check_secrets_env", return_value=None),
            patch("loops.common.preflight._check_project_path", return_value=None),
            pytest.raises(SystemExit, match="1"),
        ):
            run_fix_preflight({})

    def test_exits_1_when_project_path_missing(self) -> None:
        with (
            patch("loops.common.preflight._check_gh_auth", return_value=None),
            patch("loops.common.preflight._check_op_on_path", return_value=None),
            patch("loops.common.preflight._check_secrets_env", return_value=None),
            patch(
                "loops.common.preflight._check_project_path",
                return_value="path missing",
            ),
            pytest.raises(SystemExit, match="1"),
        ):
            run_fix_preflight({})

    def test_does_not_exit_when_all_pass(self) -> None:
        with (
            patch("loops.common.preflight._check_gh_auth", return_value=None),
            patch("loops.common.preflight._check_op_on_path", return_value=None),
            patch("loops.common.preflight._check_secrets_env", return_value=None),
            patch("loops.common.preflight._check_project_path", return_value=None),
        ):
            run_fix_preflight({})  # should not raise


class TestRunGroomPreflight:
    def test_exits_1_when_gh_auth_fails(self) -> None:
        with (
            patch("loops.common.preflight._check_gh_auth", return_value="gh auth failed"),
            patch("loops.common.preflight._check_op_on_path", return_value=None),
            patch("loops.common.preflight._check_secrets_env", return_value=None),
            pytest.raises(SystemExit, match="1"),
        ):
            run_groom_preflight()

    def test_does_not_exit_when_all_pass(self) -> None:
        with (
            patch("loops.common.preflight._check_gh_auth", return_value=None),
            patch("loops.common.preflight._check_op_on_path", return_value=None),
            patch("loops.common.preflight._check_secrets_env", return_value=None),
        ):
            run_groom_preflight()  # should not raise
