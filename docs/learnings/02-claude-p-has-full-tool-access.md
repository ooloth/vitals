# `claude -p` has full tool access in non-interactive mode

**What we assumed**: Print mode might be read-only or have reduced tool
access.

**What we found**: `claude -p` has the same tool access as interactive mode —
read files, write files, run bash commands. The Write tool works exactly as
expected when the agent is asked to write JSON to a file path.
