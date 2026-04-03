# Scan: Dead Code

Scan a codebase for code that is no longer reachable or used.

## Instructions

Explore the codebase at the path provided in the project config. Look for:

- **Unused imports**: imported names that are never referenced
- **Unused functions or methods**: defined but never called anywhere in the codebase
- **Unused variables**: assigned but never read
- **Unreachable branches**: conditions that can never be true given the surrounding logic
- **Unused files**: modules that are never imported

Focus on clear cases. Do not flag code that might be called dynamically,
used by external consumers, or referenced in ways that are hard to trace
statically — note any uncertainty in your description.

## How to explore

Use Grep to search for references to symbols you suspect are unused.
Cross-reference definitions against call sites before reporting.

## Output format

Write your output as JSON to the file path provided by the coordinator.

```json
{
  "findings": [
    {
      "pattern": "brief label for this type of dead code",
      "location": "file path and line range if known",
      "description": "what is unused and why it is safe to remove",
      "severity": "high | medium | low",
      "sample": "the unused definition or import verbatim"
    }
  ]
}
```

If nothing worth flagging is found, return `{ "findings": [] }`.
