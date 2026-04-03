# File-based output handoff

**Decision**: Agents write JSON output to a temp file path provided in the
prompt. The coordinator reads the file. Agents do not return results via
stdout.

**Why**: Parsing agent response text requires stripping markdown code fences
and is fragile when issue bodies contain embedded code blocks with their own
fences. A file write produces unambiguous, well-formed JSON. The agent uses
its native Write tool — no special output mode needed.
