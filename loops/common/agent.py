"""Claude CLI subprocess wrapper with streaming output."""

import contextlib
import dataclasses
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from loops.common.projects import ROOT


@dataclasses.dataclass
class AgentConfig:
    """Optional configuration for an agent() call."""

    max_turns: int = 20
    allowed_tools: list[str] | None = None
    transcript_path: Path | None = None
    step_name: str = ""
    timeout_minutes: float = 30


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
            if btype in ("text", "thinking"):
                sys.stdout.write(block.get("text") or block.get("thinking", ""))
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


def _stream_with_timeout(
    proc: subprocess.Popen[str],
    *,
    timeout_minutes: float,
    transcript_path: Path | None,
    label: str,
) -> None:
    """Stream subprocess stdout, killing it if *timeout_minutes* is exceeded.

    Raises TimeoutError (with *label* in the message) when the watchdog fires.
    """
    if proc.stdout is None:
        msg = "Subprocess stdout is None"
        raise RuntimeError(msg)
    timed_out = threading.Event()
    start = time.monotonic()

    def _kill_on_timeout() -> None:
        timed_out.set()
        proc.kill()

    watchdog = threading.Timer(timeout_minutes * 60, _kill_on_timeout)
    watchdog.daemon = True
    watchdog.start()
    fh = transcript_path.open("a") if transcript_path is not None else None
    try:
        for raw_line in proc.stdout:
            stripped = raw_line.strip()
            if not stripped:
                continue
            if fh is not None:
                fh.write(raw_line)
            with contextlib.suppress(json.JSONDecodeError):
                _print_event(json.loads(stripped))
    finally:
        watchdog.cancel()
        if fh is not None:
            fh.close()
    proc.wait()
    if timed_out.is_set():
        elapsed = time.monotonic() - start
        msg = f"Agent step '{label}' timed out after {elapsed:.0f}s (limit: {timeout_minutes:.0f}m)"
        raise TimeoutError(msg)


def agent(prompt_file: str, context: str, cfg: AgentConfig | None = None) -> dict:
    """Run a claude agent with the given prompt and context, returning its JSON output."""
    cfg = cfg or AgentConfig()
    prompt = (ROOT / prompt_file).read_text()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = Path(tmp.name)
    output_file.unlink()  # Let claude create it fresh; avoids mktemp race condition

    full_prompt = (
        f"{context}\n\n---\n\n{prompt}\n\n"
        f"Write your JSON output to this file: {output_file}\n"
        f"Do not include the JSON in your text response."
    )
    allowed_str = " ".join(cfg.allowed_tools) if cfg.allowed_tools else ""
    env = {
        **os.environ,
        "_PROMPT": full_prompt,
        "_TURNS": str(cfg.max_turns),
        "_ALLOWED": allowed_str,
    }
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
    _stream_with_timeout(
        proc,
        timeout_minutes=cfg.timeout_minutes,
        transcript_path=cfg.transcript_path,
        label=cfg.step_name or prompt_file,
    )
    sys.stdout.write(f"\n{'─' * 60}\n")
    sys.stdout.flush()
    if proc.returncode != 0:
        msg = f"claude subprocess exited with return code {proc.returncode}"
        raise RuntimeError(msg)
    if not output_file.exists():
        msg = f"Agent did not write output to {output_file}"
        raise RuntimeError(msg)
    text = output_file.read_text().strip()
    output_file.unlink()
    if text.startswith("```"):
        lines = text.splitlines()
        end = next((i for i in range(len(lines) - 1, 0, -1) if lines[i].strip() == "```"), None)
        text = "\n".join(lines[1:end] if end else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        msg = f"Agent ({prompt_file}) returned non-JSON output:\n{text}"
        raise RuntimeError(msg) from exc
