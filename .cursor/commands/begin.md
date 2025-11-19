# Begin Session

# Description

Initialize session with universal rules only.

# Rules to always load at startup

rules:

- .cursor/rules/core.mdc

notes:
These are minimal, always-on rules.

Do not continue to read anything else until user prompts you to do so. Feel free
to ask things like "what are we working on today?".

This repo uses uv for dependency management. Remember to use `uv run` for running scripts.

Never ever run "git add ." or "git add -A" without explicit user permission. Some files should remain untracked.

Before you git commit any files you should run:
- `uv run ruff check` and `uv run ruff format`
- `uv run mypy` for type checking

When applicable, you should use --no-pager for git commands. Otherwise you get stuck
when git output pages. Read that again: **when applicable**. --no-pager is not
applicable to all git commands. Places where it's applicable:

- git --no-pager log
- git --no-pager show SHA
- git --no-pager diff

