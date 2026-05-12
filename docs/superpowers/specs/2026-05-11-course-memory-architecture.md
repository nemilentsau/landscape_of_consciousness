# Course Continuity Architecture

Date: 2026-05-11
Updated: 2026-05-12

## Context

The consciousness course needs continuity across many NotebookLM episodes without passing every prior
research record, dossier, or transcript into every new Codex or Claude job. Earlier episodes establish
recurring distinctions such as the hard problem, phenomenal versus access consciousness, correlation
versus explanation, and physicalist versus nonphysicalist framing. Later episodes need those distinctions
as course grounding, but they should not re-research or re-explain the earlier episodes in full.

The first course-memory design used `course/course_memory.md` as a single bounded rolling summary. That
does not scale. After enough episodes, a fixed-size memory file becomes either too compressed to be useful
or too generic to guide the next episode. Repeated regeneration also risks semantic drift, duplicate
compression, and accidental promotion of one episode's speculative claims into course-level truth.

## Goals

- Keep prompt context passed to Codex and Claude bounded and relevant.
- Preserve course continuity across many episodes without compressing the whole course into one blob.
- Keep current episode research records and packets primary for factual claims.
- Make prior episode context traceable to accepted episode artifacts.
- Make it impossible to silently use placeholder research records as if they were production research.
- Keep NotebookLM as the final audio renderer, not the research or memory engine.

## Non-Goals

- Do not pass all previous `data/research/*.json` files to each episode job.
- Do not pass all previous dossiers to each episode job.
- Do not use a single ever-regenerated `course_memory.md` as the long-term source of truth.
- Do not make prior episode summaries primary evidence for new factual claims.
- Do not automate NotebookLM audio generation as part of course continuity.

## Design Principle

Course continuity is retrieval and selection, not compression alone.

The durable source of continuity should be a set of accepted, immutable episode capsules plus a small
stable course contract. For each new episode, an LLM should generate a custom context pack from selected
prior context. The context pack is bounded because it includes only the prior material relevant to the
current episode.

## Artifact Layers

### 1. Stable Course Contract

Path: `course/course_contract.md`

This is a small, mostly static operating contract for the entire course. It should stay around 500-800
words and contain:

- course purpose and audience
- factual-source-not-dialogue rule
- epistemic-status discipline
- recurring comparison axes
- NotebookLM handoff constraints
- global "do not overstate" rules

This file is not a summary of the course. It is a production contract.

### 2. Immutable Episode Capsules

Path: `course/episode_capsules/<episode-id>.json`

Each accepted episode gets one capsule after its source dossier has been reviewed and accepted. Capsules
are append-only records. They are not repeatedly rewritten into one master memory file.

Each capsule should contain:

- `episode_id`
- `title`
- `section_ids`
- `accepted_dossier_path`
- `thesis`
- `durable_concepts`
- `recurring_distinctions`
- `callbacks`
- `do_not_reexplain`
- `open_tensions`
- `epistemic_cautions`
- `useful_for_future_sections`

Capsules should be compact, roughly 300-700 words of total content. They should preserve useful prior
course anchors without trying to store full episode detail.

### 3. Callback Index

Path: `course/callback_index.json`

The callback index maps concepts to episode capsules and source paths. It lets the context generator select
relevant old material without reading every prior dossier.

Example entries:

- `hard_problem` -> `group-001`, `group-002`, relevant capsule fields
- `correlation_vs_explanation` -> `group-001`, `group-002`
- `physicalism_vs_nonphysicalism` -> `group-002`, future dualism/idealism episodes
- `combination_problem` -> panpsychism and cosmopsychism episodes

The index can be built incrementally from accepted capsules. It should point to traceable files, not invent
new course facts.

### 4. Generated Per-Episode Context Pack

Path: `episodes/<group-id>/course_context.md`

This is the bounded prompt input passed to source-dossier jobs. It is generated before an episode from:

- `course/course_contract.md`
- current `episodes/<group-id>/manifest.json`
- recent episode capsules, usually one or two
- selected older capsules via `course/callback_index.json`
- optional manually pinned callbacks

The context pack is not the source of truth. It is disposable prompt context for one episode.

Stable headings:

- `# Course Context For <group-id>`
- `## Course Contract`
- `## Current Episode Scope`
- `## Selected Prior Grounding`
- `## Relevant Callbacks`
- `## Do Not Re-Explain`
- `## Open Tensions To Preserve`
- `## Source Priority`

The source priority rule is mandatory: current research records and packets are factual sources for the
current episode; prior course context is continuity guidance for framing, pacing, and avoiding repetition.

## Required LLM Passes

### After Episode Acceptance: Capsule Generation

An LLM job creates `course/episode_capsules/<episode-id>.json` from:

- accepted `episodes/<group-id>/notebooklm_bundle/research_dossier.md`
- `episodes/<group-id>/manifest.json`
- existing `course/course_contract.md`

This pass should extract durable course continuity, not rewrite the whole course.

### Before Episode Production: Context Pack Generation

The local ordered runner creates `episodes/<group-id>/course_context.md` from:

- course contract
- current manifest
- selected episode capsules
- callback index

This deterministic selector decides what previous course material matters for the next episode. The source-dossier
LLM job receives the resulting context pack, but the context pack is not itself a research or synthesis job.

## Data Flow

1. Run episode production through `scripts/run_episode`, which enforces research jobs before source-dossier jobs.
2. Review the generated source dossier.
3. If accepted, run `accept-episode`; it runs the capsule-generation job and validates the capsule.
4. `accept-episode` updates `course/callback_index.json` from accepted capsules.
5. Before a later episode, the ordered runner generates `episodes/<group-id>/course_context.md` from selected capsules and callbacks.
6. Run the later episode through `scripts/run_episode`.

## Failure Modes To Prevent

- Treating placeholder research JSON as completed research.
- Running source-dossier jobs before research jobs.
- Passing all previous dossiers into every new job.
- Letting the context pack become a factual source for new claims.
- Recompressing all prior episodes into an increasingly vague rolling memory.
- Letting speculative claims become course-level facts without epistemic labels.

## Group 003 Transitional Design

Group 003 covers:

- 11. Quantum theories
- 12. Integrated information theory
- 13. Panpsychisms
- 14. Monisms
- 15. Dualisms

For the immediate transition, the context pack should use prior context from groups 001 and 002:

- group 001: problem framing, hard problem, phenomenal/access distinction, correlation/explanation caution
- group 002: fundamentality fork, identity theory, Kuhn's landscape, materialism, non-reductive physicalism

Group 003 should move into theories that challenge, extend, or compete with the physicalist frame while
keeping epistemic-status labels sharp.

## Validation

The architecture is implemented correctly when:

- `scripts/run_episode --episode-id group-003 --agent codex --dry-run` lists research jobs before the source-dossier job.
- The runner refuses to run the source-dossier job if any required research record contains `Research incomplete`.
- Accepted episodes can produce immutable capsule files.
- `episodes/<group-id>/course_context.md` is generated from contract, manifest, and selected capsules.
- The context pack contains source-priority language.
- Unit tests, Ruff, and Pyright pass.
