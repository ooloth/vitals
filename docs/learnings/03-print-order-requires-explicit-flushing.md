# Print order requires explicit flushing

**What happened**: Coordinator progress lines (`[scan] finding problems...`)
appeared *after* the subprocess output they were meant to precede, because
Python buffers stdout while subprocess streams directly to the terminal.

**What changed**: All coordinator `print()` calls that precede a subprocess
now use `flush=True`.
