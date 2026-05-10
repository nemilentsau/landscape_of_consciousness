# Landscape Of Consciousness

Pipeline for turning Robert Lawrence Kuhn's "A landscape of consciousness" review into a long-form podcast listening course.

The production path is:

1. Extract and segment the downloaded PDF into Kuhn's numbered theory taxonomy.
2. Generate deterministic course maps and headless-agent job manifests.
3. Run `codex exec` or `claude --bare -p` jobs to research theories and write episode scripts.
4. Use Codex Computer Use or Claude Code browser/computer control for the final NotebookLM audio handoff.

NotebookLM is a renderer at the end of the process, not the core automation layer.

## Run The Local Pipeline

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m consciousness_pipeline.cli all
```

Generated artifacts:

- `data/extracted/paper_pages.json`
- `data/extracted/headings.json`
- `data/extracted/sections.json`
- `data/research/*.json`
- `packets/theories/*.md`
- `course/exhaustive-index.md`
- `course/episode-map.md`
- `course/episode-map.json`
- `course/production-status.csv`
- `jobs/research.jsonl`
- `jobs/podcast-scripts.jsonl`
- `schemas/research-record.schema.json`
- `schemas/podcast-script.schema.json`

## Run A Headless Job

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m consciousness_pipeline.cli run-job \
  --manifest jobs/research.jsonl \
  --job-id research-9.2.3 \
  --agent codex \
  --dry-run
```

Remove `--dry-run` to execute. Use `--agent claude` to run through Claude Code headless. For Claude, configure `ANTHROPIC_API_KEY`; set `CLAUDE_ALLOWED_TOOLS` when a job needs explicit tool approval.

## NotebookLM Handoff

After research and script jobs produce `episodes/<group-id>/script.json`, use Computer Use or Claude Code browser control to create NotebookLM notebooks, upload the script/source bundle, choose Debate and Longer audio, and record the resulting URL/status in `course/production-status.csv`.
