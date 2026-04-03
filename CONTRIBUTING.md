## Requirements

- [uv](https://docs.astral.sh/uv/) (`brew install uv`) — manages the Python environment and dependencies
- [gh](https://cli.github.com/) CLI (authenticated) — (GitHub issues and PRs)
- [claude](https://docs.anthropic.com/en/docs/claude-cli) CLI (`npm install -g @anthropic-ai/claude-code`)
- `op` CLI (1Password, for secrets injection)
- A GitHub repo for each project you want the fix loop to operate on

## Install

```sh
# Clone and enter the repo
git clone https://github.com/ooloth/agency.git
cd agency

# Install dependencies (overwriting any existing ones)
uv sync --all-extras --reinstall

# Install pre-commit hooks (overwriting any existing ones)
uv run prek install --overwrite
```

## Develop

- Run checks: `uv run prek run --all-files`
- Run tests: `uv run pytest`
