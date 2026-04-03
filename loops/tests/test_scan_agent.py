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
