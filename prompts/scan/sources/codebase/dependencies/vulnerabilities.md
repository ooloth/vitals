# Scan: Dependency Vulnerabilities

Scan a project's dependencies for known security vulnerabilities.

## Instructions

Audit the project's dependencies for packages with published CVEs or
security advisories. Focus on:

- **High and critical severity CVEs**: vulnerabilities with a CVSS score
  above 7.0, or any advisory marked critical by the package ecosystem
- **Vulnerabilities in direct dependencies**: these are the project's
  responsibility to update
- **Vulnerabilities with available fixes**: a finding is only actionable if
  a patched version exists — note if no fix is available

Use the project context to understand which dependencies are exposed to
untrusted input and therefore highest risk.

## How to audit

### Python (pip-audit / uv)

```bash
pip-audit
# or
uv pip audit
```

### Node.js

```bash
npm audit --json
```

### Ruby

```bash
bundle audit check --update
```

### GitHub (if available)

```bash
gh api repos/<owner>/<repo>/vulnerability-alerts
```

## Output format

Write your output as JSON to the file path provided by the coordinator.

Include `reflections` — a list of brief observations about this step: what context was missing or ambiguous, what caused hesitation or retries, what would have made this step faster or more accurate. Return `[]` if you have nothing to add.

```json
{
  "findings": [
    {
      "pattern": "brief label for this vulnerability type",
      "location": "dependency manifest file and package name",
      "description": "CVE or advisory ID, affected versions, patched version if available",
      "severity": "high | medium | low",
      "sample": "the relevant line from the manifest verbatim"
    }
  ],
  "reflections": []
}
```

If nothing worth flagging is found, return `{ "findings": [], "reflections": [] }`.
