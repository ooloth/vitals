# `git stash` across branches causes merge conflicts

**What happened**: We stashed uncommitted changes on the `fix/issue-1` branch,
switched to `main`, and ran `git stash pop`. Git merged the stash changes with
`main`'s diverged state and produced a conflict in `loops/scan.py`.

**What we learned**: `git stash pop` is a merge. If the stashed changes
overlap with commits on the target branch, you get a conflict with no clean
way back. This is easy to trigger when bouncing between `main` and fix branches
during active development.

**What changed**: Nothing structural — this is a human workflow trap. When
working across branches, always commit or discard changes before switching.
Never stash across a branch boundary.
