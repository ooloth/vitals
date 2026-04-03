import subprocess
from unittest.mock import patch, MagicMock

import pytest

from loops.scan import agent


def test_agent_raises_on_nonzero_returncode(tmp_path):
    failed = MagicMock()
    failed.returncode = 1

    with patch("loops.common.subprocess.run", return_value=failed):
        with pytest.raises(RuntimeError, match="claude subprocess exited with return code 1"):
            agent("prompts/scans/codebase.md", "some context")
