# Scan: Outdated Dependencies

Scan a project's dependencies for packages that are significantly behind
their latest release.

## Instructions

Check the project's dependency manifest for outdated packages. Focus on:

- **Major version gaps**: packages more than one major version behind — these
  often carry breaking changes that are worth scheduling, not ignoring
- **Long-stale minor versions**: packages that haven't been updated in a year
  or more, even if no major version exists — signals neglected maintenance
- **Transitive dependencies with known upgrade paths**: direct dependencies
  that pin old versions of packages where a clear, stable upgrade exists

Do not flag every outdated package. Focus on gaps that represent real
maintenance risk or that block other upgrades. Use the project context to
understand which dependencies are most critical.

## How to check

### Python (uv / pip)

```bash
uv pip list --outdated
# or
pip list --outdated
```

### Node.js

```bash
npm outdated
```

### Ruby

```bash
bundle outdated
```

## Output format

Write your output as JSON to the file path provided by the coordinator.

```json
{
  "findings": [
    {
      "pattern": "brief label for this type of staleness",
      "location": "dependency manifest file and package name",
      "description": "current version, latest version, and why the gap matters",
      "severity": "high | medium | low",
      "sample": "the relevant line from the manifest verbatim"
    }
  ]
}
```

If nothing worth flagging is found, return `{ "findings": [] }`.
