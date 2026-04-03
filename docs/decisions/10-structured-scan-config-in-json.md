# Structured scan config in JSON with required calibration fields

**Supersedes**: [05-toml-project-registry.md](05-toml-project-registry.md)

**Decision**: Project configuration lives in `projects/projects.json`. Each
scan block carries three required arrays: `normal` (what healthy baseline
looks like), `flag` (conditions that should become issues), and `ignore`
(known noise to skip). `projects.schema.json` enforces these as required
fields on every scan block.

**Why**: The alternative — a free-form `context.md` file per project — had
no structure the schema could enforce, no convention about what to include,
and lived in a per-project folder that had no clear scope. An agent given
unstructured prose context will produce findings of inconsistent quality
across projects and scan types. Structured arrays force the author to reason
explicitly about signal versus noise before the scan runs, which is the
same reasoning the scan agent needs to do.

**Boundary**: `normal`, `flag`, and `ignore` are for load-bearing calibration
— they influence every scan run. Supplementary docs (architecture notes,
incident history, runbooks) can be referenced by path in the project config
if needed, but they are optional and unstructured by design. The required
fields exist to ensure every scan is calibrated, not to capture everything
knowable about a project.

**Cadence**: Scan cadence belongs in the cron schedule, not in the project
config. `projects.json` describes what to scan and how to interpret results;
the scheduler decides when. This keeps the two concerns separate — changing
a scan's frequency doesn't require touching the project registry.
