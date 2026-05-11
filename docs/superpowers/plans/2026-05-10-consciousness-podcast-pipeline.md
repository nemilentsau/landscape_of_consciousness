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

## Current Commands

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m consciousness_pipeline.cli all
```

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m consciousness_pipeline.cli run-job \
  --manifest jobs/research.jsonl \
  --job-id research-9.2.3 \
  --agent codex \
  --dry-run
```

## Next Work

- Run one Codex research job on a representative mainstream theory.
- Run one source-script job on the corresponding episode group.
- Add validation for completed research/source-script outputs.
- Build factual NotebookLM dossier material under `episodes/<group-id>/notebooklm_bundle/`.
- Then test a single NotebookLM handoff with Computer Use or Claude Code browser control.
