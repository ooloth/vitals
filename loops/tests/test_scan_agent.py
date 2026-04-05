from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from loops.common.agent import agent


def test_agent_raises_on_nonzero_returncode(tmp_path: Path) -> None:
    proc_mock = MagicMock()
    proc_mock.stdout = iter([])
    proc_mock.returncode = 1

    with (
        patch("loops.common.agent.subprocess.Popen", return_value=proc_mock),
        pytest.raises(RuntimeError, match="claude subprocess exited with return code 1"),
    ):
        agent("prompts/scan/sources/codebase/dead-code.md", "some context")


def test_agent_raises_with_context_on_malformed_json(tmp_path: Path) -> None:
    output_file = tmp_path / "agent_output.json"
    output_file.touch()  # so the initial unlink() succeeds

    proc_mock = MagicMock()
    proc_mock.stdout = iter([])
    proc_mock.returncode = 0
    proc_mock.wait.side_effect = lambda: output_file.write_text("this is not json")

    tmp_file_mock = MagicMock()
    tmp_file_mock.name = str(output_file)
    ntf_ctx = MagicMock()
    ntf_ctx.__enter__ = MagicMock(return_value=tmp_file_mock)
    ntf_ctx.__exit__ = MagicMock(return_value=False)

    with (
        patch("loops.common.agent.subprocess.Popen", return_value=proc_mock),
        patch("loops.common.agent.tempfile.NamedTemporaryFile", return_value=ntf_ctx),
        pytest.raises(RuntimeError, match="non-JSON output"),
    ):
        agent("prompts/scan/sources/codebase/dead-code.md", "some context")


def test_agent_writes_transcript_when_path_provided(tmp_path: Path) -> None:
    output_file = tmp_path / "agent_output.json"
    output_file.touch()  # so the initial unlink() succeeds
    transcript_file = tmp_path / "transcript.jsonl"

    lines = ['{"type": "assistant"}\n', '{"type": "result"}\n']
    proc_mock = MagicMock()
    proc_mock.stdout = iter(lines)
    proc_mock.returncode = 0
    proc_mock.wait.side_effect = lambda: output_file.write_text('{"findings": []}')

    tmp_file_mock = MagicMock()
    tmp_file_mock.name = str(output_file)
    ntf_ctx = MagicMock()
    ntf_ctx.__enter__ = MagicMock(return_value=tmp_file_mock)
    ntf_ctx.__exit__ = MagicMock(return_value=False)

    with (
        patch("loops.common.agent.subprocess.Popen", return_value=proc_mock),
        patch("loops.common.agent.tempfile.NamedTemporaryFile", return_value=ntf_ctx),
    ):
        agent(
            "prompts/scan/sources/codebase/dead-code.md",
            "some context",
            transcript_path=transcript_file,
        )

    assert transcript_file.exists()
    assert transcript_file.read_text() == "".join(lines)


def test_agent_skips_transcript_when_path_not_provided(tmp_path: Path) -> None:
    output_file = tmp_path / "agent_output.json"
    output_file.touch()  # so the initial unlink() succeeds

    proc_mock = MagicMock()
    proc_mock.stdout = iter(['{"type": "assistant"}\n'])
    proc_mock.returncode = 0
    proc_mock.wait.side_effect = lambda: output_file.write_text('{"findings": []}')

    tmp_file_mock = MagicMock()
    tmp_file_mock.name = str(output_file)
    ntf_ctx = MagicMock()
    ntf_ctx.__enter__ = MagicMock(return_value=tmp_file_mock)
    ntf_ctx.__exit__ = MagicMock(return_value=False)

    with (
        patch("loops.common.agent.subprocess.Popen", return_value=proc_mock),
        patch("loops.common.agent.tempfile.NamedTemporaryFile", return_value=ntf_ctx),
    ):
        agent("prompts/scan/sources/codebase/dead-code.md", "some context")

    assert not any(tmp_path.glob("*.jsonl"))
