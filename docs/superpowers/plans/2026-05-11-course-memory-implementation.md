# Course Continuity Implementation Plan

> **For agentic workers:** Use this plan to replace the single rolling-memory design with layered course
> continuity. Do not run source-dossier jobs inline. Production episode runs must go through
> `scripts/run_episode` or an equivalent ordered runner.

## Goal

Build a scalable course-continuity layer for the consciousness podcast pipeline.

The system should:

- run research jobs before source-dossier jobs
- reject placeholder research before dossier generation
- create immutable episode capsules only after a dossier is accepted
- generate per-episode context packs from selected prior context
- avoid a single global memory blob as the long-term source of truth

## Implemented State

Implemented in this branch:

- `scripts/run_episode`
- `consciousness_pipeline.episode_runner`
- `run-episode` CLI command
- `accept-episode` CLI command
- research-before-source-script ordering
- placeholder research validation before source-dossier execution
- static `course/course_contract.md`
- `course_episode_capsule` headless job manifest
- capsule validation and deterministic schema artifact
- explicit accepted-dossier checkpoint
- callback index generation from accepted capsules
- deterministic `episodes/<group-id>/course_context.md` renderer from contract, recent capsules, and matching callbacks

## Target Artifacts

### Course Contract

Path: `course/course_contract.md`

Small static production contract. This replaces the long-term role previously assigned to
`course/course_memory.md`.

Required headings:

- `# Consciousness Course Contract`
- `## Course Purpose`
- `## Production Rules`
- `## Epistemic Discipline`
- `## Recurring Comparison Axes`
- `## NotebookLM Handoff Rules`
- `## Global Do Not Overstate`

### Episode Capsule

Path: `course/episode_capsules/<episode-id>.json`

Created only after the episode source dossier is accepted.

Proposed schema:

```json
{
  "schema_version": "episode_capsule_v1",
  "episode_id": "group-003",
  "title": "Top-level sections Part 3",
  "section_ids": ["11", "12", "13", "14", "15"],
  "accepted_dossier_path": "episodes/group-003/notebooklm_bundle/research_dossier.md",
  "thesis": "string",
  "durable_concepts": [
    {
      "concept": "combination_problem",
      "summary": "string",
      "source_path": "episodes/group-003/notebooklm_bundle/research_dossier.md"
    }
  ],
  "recurring_distinctions": ["string"],
  "callbacks": [
    {
      "concept": "combination_problem",
      "summary": "string",
      "source_path": "episodes/group-003/notebooklm_bundle/research_dossier.md",
      "useful_for_future_sections": ["panpsychism"]
    }
  ],
  "do_not_reexplain": ["string"],
  "open_tensions": ["string"]
}
```

### Callback Index

Path: `course/callback_index.json`

Generated or updated from accepted capsules.

Proposed shape:

```json
{
  "combination_problem": [
    {
      "episode_id": "group-003",
      "capsule_path": "course/episode_capsules/group-003.json",
      "source_path": "episodes/group-003/notebooklm_bundle/research_dossier.md",
      "summary": "string"
    }
  ]
}
```

### Per-Episode Context Pack

Path: `episodes/<group-id>/course_context.md`

Generated before the episode source-dossier job from:

- `course/course_contract.md`
- current `episodes/<group-id>/manifest.json`
- recent episode capsules
- selected callback-index entries

Required headings:

- `# Course Context For <group-id>`
- `## Course Contract`
- `## Current Episode Scope`
- `## Selected Prior Grounding`
- `## Relevant Callbacks`
- `## Do Not Re-Explain`
- `## Open Tensions To Preserve`
- `## Source Priority`

## Task 1: Add Course Contract Bootstrap

Files:

- Create or modify: `consciousness_pipeline/course_contract.py`
- Create: `tests/test_course_contract.py`
- Generate: `course/course_contract.md`

Steps:

- [ ] Write tests for default contract creation.
- [ ] Implement `DEFAULT_COURSE_CONTRACT`.
- [ ] Add CLI command `write-contract`.
- [ ] Update docs to call the contract static production guidance, not course memory.

Validation:

```bash
uv run python -m unittest tests.test_course_contract -v
uv run python -m consciousness_pipeline.cli write-contract
```

## Task 2: Add Episode Capsule Schema And Validation

Files:

- Create: `schemas/episode-capsule.schema.json`
- Create: `consciousness_pipeline/episode_capsules.py`
- Create: `tests/test_episode_capsules.py`

Steps:

- [ ] Define capsule dataclass or schema-shaped validation helper.
- [ ] Validate required fields and source paths.
- [ ] Reject capsules with empty durable concepts or missing accepted dossier path.
- [ ] Keep output JSON deterministic and stable.

Validation:

```bash
uv run python -m unittest tests.test_episode_capsules -v
```

## Task 3: Add LLM Capsule Generation Job

Files:

- Modify: `consciousness_pipeline/agent_jobs.py`
- Modify: `consciousness_pipeline/agent_runner.py` if needed
- Create: `jobs/episode-capsules.jsonl`
- Create tests in `tests/test_agent_jobs.py` and `tests/test_agent_runner.py`

Steps:

- [ ] Add a `course_episode_capsule` job kind.
- [ ] Job input paths must include the accepted dossier and episode manifest.
- [ ] Job output path should be `course/episode_capsules/<episode-id>.json`.
- [ ] Prompt must say: extract durable course continuity, do not rewrite the whole course, do not add new facts.
- [ ] Output must match `schemas/episode-capsule.schema.json`.

Validation:

```bash
uv run python -m unittest tests.test_agent_jobs tests.test_agent_runner -v
```

## Task 4: Add Explicit Accept Step

Files:

- Modify: `consciousness_pipeline/cli.py`
- Create: `consciousness_pipeline/episode_acceptance.py`
- Create: `tests/test_episode_acceptance.py`

Steps:

- [ ] Add command `accept-episode --episode-id <group-id> --agent codex|claude`.
- [ ] Refuse if `episodes/<group-id>/notebooklm_bundle/research_dossier.md` is missing.
- [ ] Run the capsule-generation job.
- [ ] Write `course/episode_capsules/<episode-id>.json`.
- [ ] Update production status to mark source dossier accepted or ready for NotebookLM.

Important:

- `scripts/run_episode` must not update memory automatically.
- Acceptance is a human checkpoint. A bad source dossier must not poison future context.

Validation:

```bash
uv run python -m unittest tests.test_episode_acceptance -v
```

## Task 5: Build Callback Index From Capsules

Files:

- Create: `consciousness_pipeline/callback_index.py`
- Create: `tests/test_callback_index.py`
- Generate: `course/callback_index.json`

Steps:

- [ ] Read all accepted capsules.
- [ ] Extract callback entries into a concept-keyed index.
- [ ] Preserve traceability to capsule and accepted dossier paths.
- [ ] Keep index deterministic.

Validation:

```bash
uv run python -m unittest tests.test_callback_index -v
```

## Task 6: Generate Context Pack From Contract And Selected Capsules

Files:

- Replace or refactor: `consciousness_pipeline/course_context.py`
- Update: `tests/test_course_context.py`
- Update: `consciousness_pipeline/episode_runner.py`

Steps:

- [ ] Stop using `DEFAULT_COURSE_MEMORY` as the main context source.
- [ ] Context generation reads `course/course_contract.md`.
- [ ] It selects recent capsules and relevant callback-index entries.
- [ ] It renders the required context-pack headings.
- [ ] It keeps source-priority language mandatory.
- [ ] It remains bounded by selecting context, not by recompressing every episode.

Validation:

```bash
uv run python -m unittest tests.test_course_context tests.test_episode_runner -v
scripts/run_episode --episode-id group-003 --agent codex --dry-run
```

## Task 7: Documentation And Migration

Files:

- Update: `README.md`
- Update: `docs/superpowers/specs/2026-05-11-course-memory-architecture.md`
- Update: `course/README.md` if added

Steps:

- [ ] Explain `scripts/run_episode` as the only production episode runner.
- [ ] Explain `accept-episode` as the only memory/capsule update entry point.
- [ ] Mark `run-job` as low-level debugging/comparison only.
- [ ] Document how `course/course_memory.md` is deprecated or migrated.

## Full Quality Gate

Before claiming this work is complete:

```bash
uv run ruff check .
uv run pyright
uv run python -m unittest discover -s tests -v
git diff --check
```

## Rollout For Group 003

Correct production order:

```bash
scripts/run_episode --episode-id group-003 --agent codex
```

This must run:

1. `research-11`
2. `research-12`
3. `research-13`
4. `research-14`
5. `research-15`
6. validation that research records are substantive
7. `group-003-script`

After reviewing and accepting the generated dossier:

```bash
uv run python -m consciousness_pipeline.cli accept-episode --episode-id group-003 --agent codex
```

Only the accept step may create the group-003 episode capsule and update the callback index.
