# Agent Instructions

## Python Tooling

- Use `uv` for Python dependency management and command execution.
- Keep a dedicated `.venv` in this repo. Create or refresh it with `uv sync --extra dev`.
- Do not rely on a global Python environment for project commands.
- Run Python commands through `uv run`, for example:
  - `uv run python -m consciousness_pipeline.cli all`
  - `uv run python -m unittest discover -s tests -v`
  - `uv run ruff check .`
  - `uv run pyright`

## Quality Gate

All Python code must be checked with Ruff and Pyright.

Before claiming Python work is complete, run:

```bash
uv run ruff check .
uv run pyright
uv run python -m unittest discover -s tests -v
```

## Project Notes

- The downloaded PDF in `papers/` is a local source artifact and is not committed.
- NotebookLM is only the final audio handoff target. Research and script generation should run through headless Codex CLI or Claude Code jobs.
- Keep generated research records schema-shaped so they can be consumed by packet and script generation.
