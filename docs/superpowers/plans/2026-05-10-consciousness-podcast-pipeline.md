# Consciousness Podcast Pipeline Implementation Plan

Goal: build a reproducible production pipeline that starts from Kuhn's downloaded PDF, uses Codex CLI and Claude Code headless jobs for research and factual source-script generation, and reserves NotebookLM for the final dialogue/audio handoff.

## Architecture

- Python package for deterministic local artifacts.
- JSON/JSONL/CSV as resumable state.
- `codex exec` and `claude -p` as execution backends.
- Computer Use or Claude Code browser control only after factual NotebookLM dossiers are generated.

## Completed Foundation

- PDF extraction to page-aware JSON.
- Heading detection for numbered theory taxonomy.
- Section segmentation with taxonomy paths.
- Packet rendering and validation.
- Episode grouping and production status CSV.
- Headless research and source-script job manifests.
- JSON schemas for research records and source scripts.
- Command builders for Codex CLI and Claude Code headless.
- Ordered episode runner that executes research jobs before source-dossier jobs.
- Placeholder research validation before source-dossier execution.

## Current Commands

```bash
uv run python -m consciousness_pipeline.cli all
```

Production episode run:

```bash
scripts/run_episode --episode-id group-003 --agent codex --dry-run
```

Low-level single-job debugging only:

```bash
uv run python -m consciousness_pipeline.cli run-job \
  --manifest jobs/research.jsonl \
  --job-id research-9.2.3 \
  --agent codex \
  --dry-run
```

## Next Work

- Replace single rolling course memory with course contract, accepted episode capsules, callback index,
  and generated context packs.
- Add explicit episode acceptance step before any course-continuity state is updated.
- Run group 003 through `scripts/run_episode` only after the above document and plan updates are accepted.
- Build factual NotebookLM dossier material under `episodes/<group-id>/notebooklm_bundle/`.
- Then test a single NotebookLM handoff with Computer Use or Claude Code browser control.
