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

Tests must be meaningful behavioral checks, not coverage padding. Before adding or changing tests, use the
project testing guidance in `.claude/skills/testing/SKILL.md` and make sure each test would catch a real
regression. Prefer assertions on outcomes, persisted artifacts, validation errors, and state transitions.
Cover important branches, boundaries, and failure modes; remove redundant tests that exercise the same
equivalence class. Do not add brittle prompt-string checks, mock-call checks, or snapshots unless they are
the only practical way to protect a real contract.

Before claiming Python work is complete, run:

```bash
uv run ruff check .
uv run pyright
uv run python -m unittest discover -s tests -v
```

## Project Notes

- The downloaded PDF in `papers/` is a local source artifact and is not committed.
- NotebookLM is only the final audio handoff target. Research and script generation should run through headless Codex CLI or Claude Code jobs.
- For NotebookLM audio, use Deep Dive format with Long length. Do not choose Debate as the NotebookLM format; debate-style balance belongs in the custom prompt.
- For NotebookLM audio handoff, upload the full bundle as separate files: `episodes/<group-id>/notebooklm_bundle/research_dossier.md` plus every Markdown file in `episodes/<group-id>/notebooklm_bundle/sources/`. For the current top-level episode pattern this is six files total.
- Do not concatenate, paste, summarize, or otherwise collapse the NotebookLM bundle into one copied-text source. A one-source NotebookLM notebook is invalid for this project unless the user explicitly asks for that degraded mode in the same turn.
- Every Codex-run NotebookLM handoff must end by recording the verified state with `uv run python -m consciousness_pipeline.cli record-notebooklm-status --episode-id <group-id> --audio-status audio_requested --notebook-url <url> --message "<evidence note>"`. Do not leave a handoff at `not_started` after NotebookLM has accepted an audio request.
- Do not claim the NotebookLM file picker is blocked unless a real browser or OS file picker path has been attempted and the actual error has been reported. If browser automation cannot set files through the extension, use a native/browser file picker path or stop and ask the user to take over that upload step; do not substitute copied text.
- Keep generated research records schema-shaped so they can be consumed by packet and script generation.

## Production Pipeline Rules

- Do not run episode production through inline shell snippets or ad hoc one-off command sequences.
- Use `scripts/run_episode --episode-id <group-id> --agent codex|claude` for production episode runs.
- Run exactly one episode unless the user explicitly asks for a batch.
- The ordered runner must preserve this sequence:
  1. generate or refresh `episodes/<group-id>/course_context.md`
  2. run every required `research-<section-id>` job
  3. validate that research records are substantive and not placeholders
  4. run the single `group-id-script` source-dossier job
- `run-job` is low-level debugging/comparison only. Do not use it as the production path for a whole episode.
- `script.json` is a historical artifact name. Its content must be factual NotebookLM source material, especially `research_dossier_markdown`; do not create dialogue, host banter, stage directions, or performed scripts.
- Job kinds, manifest filenames, schema filenames, prompt contracts, allowed headless agents, and JSON schema objects must stay centralized in `consciousness_pipeline/agents/contracts.py` and `consciousness_pipeline/contracts/schemas.py`.
- Treat `jobs/*.jsonl` and `schemas/*.json` as generated runtime artifacts. Refresh them with `uv run python -m consciousness_pipeline.cli jobs`; do not hand-edit them or add duplicate CLI constants.
- Job rows must not carry `schema_path`. Runners and prompts derive schema paths from the job kind through the contract registry.

## Course Continuity Rules

- Do not recreate or rely on `course/course_memory.md`.
- Long-term continuity lives in:
  - `course/course_contract.md`
  - `course/episode_capsules/<group-id>.json`
  - `course/callback_index.json`
- Only run `uv run python -m consciousness_pipeline.cli accept-episode --episode-id <group-id> --agent codex|claude` after the user has accepted a generated source dossier.
- `accept-episode` is the only production command that may create or update episode capsules and callback indexes.
- Prior continuity is framing guidance, not evidence. Current research records and current packet inputs remain the factual sources for the current episode.

## Headless Agent Rules

- Use the locally installed/authenticated Codex CLI or Claude Code CLI.
- Do not tell the user to configure API keys for Claude Code headless unless an actual CLI error proves local auth is unavailable.
- Claude Code should run in normal print mode through the project runner; do not use `--bare` unless the user explicitly requests it.
