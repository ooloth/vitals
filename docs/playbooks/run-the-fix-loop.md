# Run the fix loop on an issue

1. Ensure the issue is labelled `ready-for-agent` in GitHub so the fix loop can find it.

2. Run:

   ```bash
   uv run --frozen python run.py fix --issue <number>
   ```

   Or let it pick the next open `ready-for-agent` issue:

   ```bash
   uv run --frozen python run.py fix
   ```

3. The loop will implement, review, and revise until approved or escalated.
   Watch the streaming output to follow progress.

4. If the loop escalates (exits non-zero), check the issue for complexity that
   requires human judgment, then either simplify the issue scope or handle it
   manually.
