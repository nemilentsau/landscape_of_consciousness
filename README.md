# Landscape Of Consciousness

Pipeline for turning Robert Lawrence Kuhn's "A landscape of consciousness" review into a long-form podcast listening course.

The production path is:

1. Extract and segment the downloaded PDF into Kuhn's numbered theory taxonomy.
2. Generate deterministic course maps and headless-agent job manifests.
3. Run `codex exec` or `claude --bare -p` jobs to research theories and write factual source scripts.
4. Use Codex Computer Use or Claude Code browser/computer control for the final NotebookLM audio handoff.

NotebookLM is the dialogue and audio renderer at the end of the process, not the core automation layer.
The local script artifacts are factual research dossiers for NotebookLM, not performed dialogue scripts.

## Run The Local Pipeline

```bash
uv sync --extra dev
uv run python -m consciousness_pipeline.cli all
```

Generated artifacts:

- `data/extracted/paper_pages.json`
- `data/extracted/headings.json`
- `data/extracted/sections.json`
- `data/research/README.md`
- `data/research/*.json`
- `packets/theories/*.md`
- `course/exhaustive-index.md`
- `course/episode-map.md`
- `course/episode-map.json`
- `course/production-status.csv`
- `episodes/<group-id>/manifest.json`
- `episodes/<group-id>/README.md`
- `jobs/research.jsonl`
- `jobs/source-scripts.jsonl`
- `schemas/research-record.schema.json`
- `schemas/source-script.schema.json`

Research JSON files are section-level inputs, not podcast episodes. Episode directories show how
those section inputs are assembled into a single listening-course episode.

## Run A Headless Job

```bash
uv run python -m consciousness_pipeline.cli run-job \
  --manifest jobs/research.jsonl \
  --job-id research-9.2.3 \
  --agent codex \
  --dry-run
```

Remove `--dry-run` to execute. Use `--agent claude` to run through Claude Code headless. For Claude, configure `ANTHROPIC_API_KEY`; set `CLAUDE_ALLOWED_TOOLS` when a job needs explicit tool approval.

## Quality Checks

```bash
uv run ruff check .
uv run pyright
uv run python -m unittest discover -s tests -v
```

## NotebookLM Handoff

After research and source-script jobs produce `episodes/<group-id>/script.json` and
`episodes/<group-id>/notebooklm_bundle/research_dossier.md`, generate factual per-section Markdown
sources for the same bundle:

```bash
uv run python -m consciousness_pipeline.cli bundle-sources --episode-id group-001
```

Use Computer Use or Claude Code browser control to create NotebookLM notebooks, upload
`research_dossier.md` plus every Markdown file in `notebooklm_bundle/sources/`, choose Deep Dive and
Long audio, paste the custom prompt from the episode manifest, and record the resulting URL/status in
`course/production-status.csv`.
