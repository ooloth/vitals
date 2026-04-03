import json
import subprocess
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent.parent


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
                print(block["text"], end="", flush=True)
            elif btype == "tool_use":
                name = block.get("name", "?")
                inp = block.get("input", {})
                if name == "Bash":
                    cmd = inp.get("command", "").split("\n")[0][:100]
                    print(f"\n  $ {cmd}", flush=True)
                elif name in ("Read", "Edit", "Write"):
                    print(f"\n  [{name}] {inp.get('file_path', '?')}", flush=True)
                elif name in ("Glob", "Grep"):
                    print(f"\n  [{name}] {inp.get('pattern', '?')}", flush=True)
                else:
                    print(f"\n  [{name}]", flush=True)
    elif etype == "result":
        print(flush=True)


def agent(prompt_file: str, context: str, max_turns: int = 20, allowed_tools: list[str] | None = None) -> dict:
    prompt = (ROOT / prompt_file).read_text()
    output_file = Path(tempfile.mktemp(suffix=".json"))
    full_prompt = (
        f"{context}\n\n---\n\n{prompt}\n\n"
        f"Write your JSON output to this file: {output_file}\n"
        f"Do not include the JSON in your text response."
    )
    cmd = ["claude", "-p", full_prompt, "--max-turns", str(max_turns), "--output-format", "stream-json"]
    if allowed_tools:
        cmd += ["--allowedTools"] + allowed_tools
    print(f"\n{'─' * 60}", flush=True)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, cwd=ROOT)
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            _print_event(json.loads(line))
        except json.JSONDecodeError:
            pass
    proc.wait()
    print(f"\n{'─' * 60}", flush=True)
    if proc.returncode != 0:
        raise RuntimeError(f"claude subprocess exited with return code {proc.returncode}")
    if not output_file.exists():
        raise RuntimeError(f"Agent did not write output to {output_file}")
    result = json.loads(output_file.read_text())
    output_file.unlink()
    return result


def load_project(project_id: str) -> dict:
    config = tomllib.loads((ROOT / "projects/projects.toml").read_text())
    project = next((p for p in config["projects"] if p["id"] == project_id), None)
    if project is None:
        raise ValueError(f"Project '{project_id}' not found in projects.toml")
    if "path" in project:
        project["path"] = str(Path(project["path"]).expanduser().resolve())
    return project
