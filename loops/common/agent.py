"""Claude CLI subprocess wrapper with streaming output."""

import contextlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from loops.common.projects import ROOT


def _print_event(event: dict) -> None:
    """Print a stream-json event from claude in a readable format.

    The --output-format stream-json schema is inferred from observed behaviour,
    not from formal documentation. This parser is best-effort: unknown event
    types and content block types are silently ignored. If tool calls or text
    are not appearing as expected, temporarily switch agent() to subprocess.run
    without --output-format to see the raw output and compare.
    """
    etype = event.get("type")
    if etype == "assistant":
        for block in event.get("message", {}).get("content", []):
            btype = block.get("type")
            if btype == "text":
                sys.stdout.write(block["text"])
                sys.stdout.flush()
            elif btype == "tool_use":
                name = block.get("name", "?")
                inp = block.get("input", {})
                if name == "Bash":
                    cmd = inp.get("command", "").split("\n")[0][:100]
                    sys.stdout.write(f"\n  $ {cmd}\n")
                    sys.stdout.flush()
                elif name in ("Read", "Edit", "Write"):
                    sys.stdout.write(f"\n  [{name}] {inp.get('file_path', '?')}\n")
                    sys.stdout.flush()
                elif name in ("Glob", "Grep"):
                    sys.stdout.write(f"\n  [{name}] {inp.get('pattern', '?')}\n")
                    sys.stdout.flush()
                else:
                    sys.stdout.write(f"\n  [{name}]\n")
                    sys.stdout.flush()
    elif etype == "result":
        sys.stdout.write("\n")
        sys.stdout.flush()


def agent(
    prompt_file: str, context: str, max_turns: int = 20, allowed_tools: list[str] | None = None
) -> dict:
    """Run a claude agent with the given prompt and context, returning its JSON output."""
    prompt = (ROOT / prompt_file).read_text()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = Path(tmp.name)
    output_file.unlink()  # Let claude create it fresh; avoids mktemp race condition

    full_prompt = (
        f"{context}\n\n---\n\n{prompt}\n\n"
        f"Write your JSON output to this file: {output_file}\n"
        f"Do not include the JSON in your text response."
    )
    allowed_str = " ".join(allowed_tools) if allowed_tools else ""
    env = {**os.environ, "_PROMPT": full_prompt, "_TURNS": str(max_turns), "_ALLOWED": allowed_str}
    sys.stdout.write(f"\n{'─' * 60}\n")
    sys.stdout.flush()
    proc = subprocess.Popen(
        [
            "/bin/sh",
            "-c",
            'claude --verbose -p "$_PROMPT" --max-turns "$_TURNS"'
            " --output-format stream-json${_ALLOWED:+ --allowedTools $_ALLOWED}",
        ],
        stdout=subprocess.PIPE,
        text=True,
        cwd=ROOT,
        env=env,
    )
    if proc.stdout is None:
        msg = "Subprocess stdout is None"
        raise RuntimeError(msg)
    for raw_line in proc.stdout:
        stripped = raw_line.strip()
        if not stripped:
            continue
        with contextlib.suppress(json.JSONDecodeError):
            _print_event(json.loads(stripped))
    proc.wait()
    sys.stdout.write(f"\n{'─' * 60}\n")
    sys.stdout.flush()
    if proc.returncode != 0:
        msg = f"claude subprocess exited with return code {proc.returncode}"
        raise RuntimeError(msg)
    if not output_file.exists():
        msg = f"Agent did not write output to {output_file}"
        raise RuntimeError(msg)
    result = json.loads(output_file.read_text())
    output_file.unlink()
    return result
