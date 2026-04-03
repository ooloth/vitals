# Deterministic Python coordinator, not agent-driven control flow

**Decision**: Loops are sequenced by short Python functions. Each step is an
explicit `agent()` call. The coordinator decides what runs next based on
structured output.

**Why**: An unattended loop cannot recover from a bad decision the way an
interactive session can. If control flow lives in the agent's interpretation
of markdown, a misread skips a step silently. Python makes sequencing
auditable, testable, and predictable.

**Boundary**: The coordinator checks `ready`, `approved`, and `findings` — it
never interprets content. Routing logic that reads the substance of agent
output belongs in a prompt, not in Python.
