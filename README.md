# landscape_of_consciousness

Pipeline for turning Robert Lawrence Kuhn's "A landscape of consciousness" review into NotebookLM-ready consciousness theory packets and podcast groups.

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
- `course/notebook-groups.md`
- `course/notebook-groups.json`
- `course/production-status.csv`

## NotebookLM Automation

Run a dry run first:

```bash
npm install
npm run notebooklm:dry-run
```

Live NotebookLM automation is intentionally run only after local packets and course groups have been reviewed.
