# Scan: Duplication

Scan a codebase for duplicated logic that could be consolidated.

## Instructions

Explore the codebase at the path provided in the project config. Look for:

- **Identical logic blocks**: the same sequence of operations copy-pasted in
  two or more places
- **Near-identical functions**: functions that do essentially the same thing
  with minor variation that could be parameterised
- **Repeated inline patterns**: the same multi-step pattern repeated inline
  rather than extracted into a helper

Focus on semantic duplication — code that means the same thing — not just
textual similarity. Two loops that happen to look alike but do unrelated
things are not duplication. A consolidation is only worth flagging if there
is a clear, non-speculative way to remove the duplication.

## How to explore

Use Grep to find repeated patterns. Read surrounding context before reporting
to confirm the duplication is genuine.

## Output format

Write your output as JSON to the file path provided by the coordinator.

```json
{
  "findings": [
    {
      "pattern": "brief label for this type of duplication",
      "location": "file paths and line ranges of all duplicated sites",
      "description": "what is duplicated and what consolidation would look like",
      "severity": "high | medium | low",
      "sample": "one of the duplicated blocks verbatim"
    }
  ]
}
```

If nothing worth flagging is found, return `{ "findings": [] }`.
