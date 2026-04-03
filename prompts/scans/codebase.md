# Scan: Codebase Improvements

Scan a codebase for concrete improvements worth making.

## Instructions

Explore the codebase at the path provided in the project config. Look for:

- **Dead code**: unused functions, variables, imports, or files
- **Obvious bugs**: off-by-one errors, unchecked nulls, wrong types
- **Missing tests**: important logic with no test coverage
- **Duplication**: near-identical code that could be consolidated
- **Complexity**: functions doing too many things, unclear naming

Focus on things that are clearly worth fixing — not style preferences or
speculative improvements. Each finding should have an obvious correct action.

## How to explore

Use your file reading and search tools to navigate the codebase. Start with:
1. The root directory structure
2. Any README or architecture docs
3. The main entry points
4. Then dig into areas that look problematic

## Output format

Respond with JSON only. No prose.

```json
{
  "findings": [
    {
      "pattern": "brief label for this type of problem",
      "location": "file path and line range if known",
      "description": "what is wrong and why it matters",
      "severity": "high | medium | low",
      "sample": "relevant code snippet or filename"
    }
  ]
}
```

If nothing worth flagging is found, return `{ "findings": [] }`.
