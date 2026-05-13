# Landscape Of Consciousness

Pipeline for turning Robert Lawrence Kuhn's "A landscape of consciousness" review into a long-form podcast listening course.

The production path is:

1. Extract and segment the downloaded PDF into Kuhn's numbered theory taxonomy.
2. Generate deterministic course maps and headless-agent job manifests.
3. Run the ordered episode runner to research theories first, validate research records, then write factual source scripts.
4. Review and accept the completed source dossier, which creates an immutable continuity capsule and callback index.
5. Use Codex Computer Use or Claude Code browser/computer control for the final NotebookLM audio handoff.

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
- `course/course_contract.md`
- `course/production-status.csv`
- `episodes/<group-id>/manifest.json`
- `episodes/<group-id>/README.md`
- `jobs/research.jsonl`
- `jobs/source-scripts.jsonl`
- `jobs/episode-reviews.jsonl`
- `jobs/episode-capsules.jsonl`
- `schemas/research-record.schema.json`
- `schemas/source-script.schema.json`
- `schemas/episode-review.schema.json`
- `schemas/episode-capsule.schema.json`

Research JSON files are section-level inputs, not podcast episodes. Episode directories show how
those section inputs are assembled into a single listening-course episode.

## Run An Episode In The Correct Order

Use the episode runner for production. It runs every required section research job first, checks that the
resulting `data/research/<section-id>.json` records are no longer placeholders, and only then runs the
episode source-dossier job.

```bash
scripts/run_episode --episode-id group-003 --agent codex
```

For an end-to-end production run with a separate reviewer gate, use Codex for generation and Claude
Code for review plus continuity acceptance:

```bash
scripts/run_episode --episode-id group-004 --agent codex --auto-accept
```

With `--auto-accept`, the runner validates the generated source dossier, writes NotebookLM source
files, asks the review agent to approve or reject `episodes/<group-id>/review.json`, and only then
runs the capsule job that updates course continuity. The review agent defaults to Claude Code and can
be overridden with `--review-agent`. A rejected review stops before `course/episode_capsules/<group-id>.json`
or `course/callback_index.json` are updated.

Preview the job order without executing anything:

```bash
scripts/run_episode --episode-id group-003 --agent codex --dry-run
```

If any research record still contains `Research incomplete`, the runner stops before the source-dossier
step. Do not manually run an episode source-dossier job before the research jobs have completed and passed
this gate.

## Manually Accept A Finished Episode Dossier

If you do not use `--auto-accept`, accept a reviewed source dossier before using it as continuity for
later episodes:

```bash
uv run python -m consciousness_pipeline.cli accept-episode --episode-id group-002 --agent codex
```

This command and `scripts/run_episode --auto-accept` are the production entry points that may create
`course/episode_capsules/<group-id>.json` and update `course/callback_index.json`. Acceptance remains
the checkpoint that prevents a bad dossier from poisoning future context; the automated path delegates
that checkpoint to the configured review agent.

`course/course_memory.md` has been removed from the active pipeline. Durable continuity now lives in the
static `course/course_contract.md`, immutable accepted episode capsules, and the generated callback index.

## Run A Single Headless Job For Debugging

`run-job` is the low-level primitive. Use it for isolated research jobs, comparison artifacts, or debugging,
not as the production path for a whole episode.

```bash
uv run python -m consciousness_pipeline.cli run-job \
  --manifest jobs/research.jsonl \
  --job-id research-9.2.3 \
  --agent codex \
  --dry-run
```

Remove `--dry-run` to execute. Use `--agent claude` to run through the installed/authenticated
Claude Code CLI in normal print mode. The runner intentionally does not use `--bare`, because
`--bare` bypasses Claude Code's usual local auth/keychain path and forces API-key-style auth.

To generate a comparison artifact without overwriting the Codex output, override the output paths:

```bash
uv run python -m consciousness_pipeline.cli run-job \
  --manifest jobs/source-scripts.jsonl \
  --job-id group-002-script \
  --agent claude \
  --output-path episodes/group-002/claude/script.json \
  --bundle-output-path episodes/group-002/claude/notebooklm_bundle/research_dossier.md
```

## Quality Checks

```bash
uv run ruff check .
uv run pyright
uv run python -m unittest discover -s tests -v
```

## NotebookLM Handoff

After research and source-dossier jobs produce `episodes/<group-id>/script.json` and
`episodes/<group-id>/notebooklm_bundle/research_dossier.md`, generate factual per-section Markdown
sources for the same bundle:

```bash
uv run python -m consciousness_pipeline.cli bundle-sources --episode-id group-001
```

Use Computer Use or Claude Code browser control to create NotebookLM notebooks, upload
`research_dossier.md` plus every Markdown file in `notebooklm_bundle/sources/`, choose Deep Dive and
Long audio, paste the custom prompt from the episode manifest, and record the resulting URL/status in
`course/production-status.csv`.
