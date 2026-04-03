# Scan: Missing Tests

Scan a codebase for important logic that has no test coverage.

## Instructions

Explore the codebase at the path provided in the project config. Look for:

- **Untested branching logic**: conditionals that determine whether something
  succeeds or fails, with no test exercising each branch
- **Untested error paths**: exception handling, fallback behaviour, or failure
  modes that are never asserted against
- **Untested public interfaces**: functions or methods that are part of the
  public API of a module but have no corresponding test
- **Tests that don't assert**: test functions that run code but make no
  assertions — they pass vacuously

Use the project context to calibrate what counts as "important". Not every
helper needs a test; coordinator logic, error handling, and anything
externally visible does.

## How to explore

Start with the test directory to understand what is currently covered.
Cross-reference against the main source files to find gaps.

## Output format

Write your output as JSON to the file path provided by the coordinator.

```json
{
  "findings": [
    {
      "pattern": "brief label for this type of coverage gap",
      "location": "file path and line range of the untested logic",
      "description": "what is not covered and why it matters",
      "severity": "high | medium | low",
      "sample": "the untested code path verbatim"
    }
  ]
}
```

If nothing worth flagging is found, return `{ "findings": [] }`.
