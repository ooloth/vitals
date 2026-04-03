# Prompts as the primary extension point

**Decision**: Adding a new scan type means adding a `prompts/scans/<type>.md`
file. Adding a new step means adding a prompt and one `agent()` call.

**Why**: A prompt is the right level of abstraction for evolving analytical
judgment. It is readable, diffable, and testable by running the loop.
Encapsulating the same logic in Python would make it harder to read and
require a code change to adjust what the agent looks for.
