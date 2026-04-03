# Implement

Implement a fix for a GitHub issue.

## Instructions

You will receive a GitHub issue and a branch name. Your job is to:

1. Understand the problem described
2. Find the relevant code by searching for the snippet in the issue — do not
   trust file paths or line numbers, which may have shifted; locate by symbol
   name or by grepping for the code itself
3. Make the minimal changes needed to address the issue
4. Prefer the simplest solution. If the problem can be avoided entirely (e.g.
   by choosing a different value, removing a constraint, or sidestepping the
   issue), that is better than adding handling for a problem that shouldn't
   need to exist
5. The branch has already been created and checked out for you — do not create
   a new branch; commit your changes to the branch you are on
6. Ensure existing tests pass; add a test if the fix is non-trivial
7. Do not fix anything not described in the issue

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
