# Debug a failed agent step

Agent steps stream output to the terminal. If a step fails:

1. Look at the streaming output just before the failure — the agent usually
   explains what it attempted.

2. Check whether the temp file was written:
   ```bash
   ls /tmp/*.json
   ```
   If no file exists, the agent hit its `--max-turns` limit or encountered a
   tool error before writing output.

3. Re-run with a higher `max_turns` if the agent ran out of turns:
   Edit the `agent()` call in the relevant coordinator and increase the default.

4. If the output file exists but is malformed JSON, inspect it:
   ```bash
   cat /tmp/<file>.json
   ```
   The agent may have written a partial result before a tool call failed.
