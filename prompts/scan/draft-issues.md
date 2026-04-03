# Draft Issues

Write GitHub issue drafts from triaged findings.

## Instructions

You will receive triaged clusters. For each cluster that warrants a GitHub
issue, write a clear, actionable issue using the three-section structure below.

## Structure

### Problem

One paragraph: what is wrong and why it matters. Include the problematic code
verbatim inline as evidence — greppable, so the implementer can find it by
searching rather than by trusting a file path or line number that may have
shifted.

### Definition of done

Describe what the fixed state looks like from the outside. Frame it as:
*"you know this is fixed when..."* — observable outcomes, not implementation
prescriptions. This is not an exhaustive checklist; it is the key proof that
the problem is gone. Implementers and reviewers can go beyond it.

### Out of scope

What not to change. Protects the implementer from over-engineering and the
reviewer from scope creep. Be specific — name the related concerns that are
tracked elsewhere or intentionally deferred.

---

## Rules

**Reference by snippet, never by location.** File paths and line numbers go
stale the moment any other issue is resolved. The code snippet is stable.

**Definition of done is outside-in.** Each proof point describes something
you can observe by running the code — not something you can verify by reading
it. "Run X, see Y" not "the code now does Z."

**Titles name the problem, not the solution.** A good title makes the problem
legible; a bad title prescribes the fix. "Subprocess failures surface as
cryptic JSONDecodeError" is better than "Add check=True to subprocess calls."

---

## Output format

Write your output as JSON to the file path provided by the coordinator.

```json
{
  "issues": [
    {
      "title": "short, specific problem statement — not a solution",
      "body": "markdown body following the three-section structure above",
      "label": "sev:critical | sev:high | sev:medium | sev:low"
    }
  ]
}
```

One cluster = one issue. Do not bundle unrelated problems.
