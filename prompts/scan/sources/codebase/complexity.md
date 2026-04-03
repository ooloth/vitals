# Scan: Complexity

Scan a codebase for code that is harder to understand than it needs to be.

## Instructions

Explore the codebase at the path provided in the project config. Look for:

- **Overloaded functions**: functions that do more than one thing and could be
  split without losing cohesion
- **Deep nesting**: conditionals or loops nested more than two or three levels
  deep where flattening would improve readability
- **Misleading names**: variables, functions, or modules whose names suggest
  something different from what they do
- **Implicit magic**: values or behaviours that are not explained and would
  surprise a reader unfamiliar with the code

Focus on complexity that causes real confusion, not style preferences. A
finding is worth reporting only if a reader would genuinely misunderstand
or struggle with the code as written.

## How to explore

Read the main entry points and work inward. Pay attention to anything that
made you slow down or re-read.

## Output format

Write your output as JSON to the file path provided by the coordinator.

```json
{
  "findings": [
    {
      "pattern": "brief label for this type of complexity",
      "location": "file path and line range if known",
      "description": "what makes this hard to understand and how it could be clearer",
      "severity": "high | medium | low",
      "sample": "the confusing code verbatim"
    }
  ]
}
```

If nothing worth flagging is found, return `{ "findings": [] }`.
