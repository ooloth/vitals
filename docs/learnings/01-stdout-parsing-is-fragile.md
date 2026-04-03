# Parsing agent output via stdout is fragile

**What happened**: The first implementation of `agent()` used
`--output-format json` and parsed `outer["result"]` from the Claude CLI
envelope. When issue bodies contained embedded code blocks, the markdown
fence-stripping logic found an inner ` ``` ` instead of the outer closing
fence and produced a `JSONDecodeError`.

**What we learned**: Agent text output is not a reliable JSON transport once
prompts produce content with embedded markdown. The output format is not under
our control.

**What changed**: Agents now write JSON to a temp file path provided in the
prompt. The coordinator reads the file. No text parsing required.
