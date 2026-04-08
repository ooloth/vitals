"""Shared step execution for all agent loops."""

import dataclasses
import time
from pathlib import Path
from typing import Protocol

from loops.common.agent import AgentConfig, agent
from loops.common.logs import write_step


class StepCtx(Protocol):
    """Minimal interface a run context must expose for step().

    Any dataclass with these three fields satisfies this protocol.
    """

    run_dir: Path
    steps: list[dict]
    refs: list[dict]


def step(
    ctx: StepCtx,
    name: str,
    prompt: str,
    content: str,
    cfg: AgentConfig | None = None,
) -> dict:
    """Run one agent step: time it, persist output, collect reflections."""
    cfg = dataclasses.replace(
        cfg or AgentConfig(),
        transcript_path=ctx.run_dir / f"{name}-transcript.jsonl",
        step_name=name,
    )
    t0 = time.monotonic()
    out = agent(prompt, content, cfg)
    ctx.steps.append({"name": name, "duration_seconds": round(time.monotonic() - t0, 1)})
    write_step(ctx.run_dir, name, out)
    ctx.refs.extend({"step": name, "text": r} for r in out.get("reflections", []))
    return out
