# Implement

Implement a fix for a GitHub issue.

## Instructions

You will receive a GitHub issue. Your job is to:

1. Understand the problem described
2. Find the relevant code
3. Implement a fix on a new branch named `fix/issue-<number>`
4. Ensure existing tests pass; add a test if the fix is non-trivial
5. Do not fix anything not described in the issue

## Output format

Write your output as JSON to the file path provided by the coordinator.

```json
{
  "branch": "fix/issue-42",
  "pr_title": "fix: <short description>",
  "pr_body": "markdown — what changed and why, closes #<number>",
  "confidence": "high | medium | low",
  "notes": "anything the reviewer should know"
}
```
