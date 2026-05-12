# Course Memory Architecture

Date: 2026-05-11

## Context

The consciousness course should stay coherent across many NotebookLM episodes without passing every previous research record or dossier into every new agent job. Earlier episodes establish recurring distinctions such as the hard problem, phenomenal versus access consciousness, correlation versus explanation, and physicalist versus nonphysicalist framing. Later episodes need those distinctions as course grounding, but they should not re-research or re-explain the earlier episodes in full.

The current pipeline already supports a per-episode context path. Source-dossier prompts read `episodes/<group-id>/course_context.md` when it exists, and the dossier prompt now requires a separate `## Course Continuity Grounding` section. Group 002 has a hand-authored context file, which proves the shape but does not scale.

## Goals

- Keep context passed to Codex and Claude source-dossier jobs bounded.
- Preserve course continuity as the series grows beyond a few episodes.
- Make current episode sources primary: current research records and packets remain the main evidence.
- Keep prior episodes available as traceable context, not as bulk prompt input.
- Document the final architecture now while implementing the simpler rolling-summary phase first.

## Non-Goals

- Do not pass all previous `data/research/*.json` files to each episode job.
- Do not make prior dossiers primary sources for new factual claims.
- Do not add vector search or retrieval infrastructure in the first implementation pass.
- Do not automate NotebookLM audio generation as part of course memory.

## Final Architecture

The final design has three layers:

1. `course/course_memory.md`
   - A bounded, curated course memory.
   - Stores durable concepts already introduced, recurring distinctions, open tensions, episode ledger entries, and "do not re-explain" rules.
   - Updated after an episode dossier has been reviewed and accepted.

2. `episodes/<group-id>/course_context.md`
   - A per-episode prompt input generated from the course memory plus the current episode manifest.
   - Summarizes what prior episodes already covered, what the current episode should not redo, and how the current episode transitions from the course so far.
   - Kept short enough to pass to every agent safely.

3. `course/callback_index.json`
   - Deferred final-design layer for selective callbacks.
   - Maps concepts to prior episode anchors and local paths, for example "explanatory gap" to `group-001`, `group-002`, and exact dossier headings.
   - Later source-dossier jobs should pull only a few relevant callbacks instead of full prior dossiers.

## Phase 1 Scope

Start with option 2: rolling summary only.

Phase 1 creates and uses:

- `course/course_memory.md`
- `episodes/group-003/course_context.md`
- a deterministic context renderer and CLI command
- job manifests that list the course context as an input path

Phase 1 does not implement `course/callback_index.json`. The architecture document keeps it visible so later work has a target shape.

## Data Flow

1. After an episode is accepted, the course memory is updated with a short durable summary.
2. Before running an episode source-dossier job, generate `episodes/<group-id>/course_context.md`.
3. The source-dossier job receives:
   - current episode research records
   - current episode packets
   - current episode manifest
   - per-episode course context
4. The generated dossier must include `## Course Continuity Grounding` as a separate top-level section.
5. After the dossier is accepted, update the course memory before moving to the next episode.

## Course Memory Format

`course/course_memory.md` should use stable headings:

- `# Consciousness Course Memory`
- `## Durable Concepts Introduced`
- `## Recurring Distinctions`
- `## Episode Ledger`
- `## Open Tensions`
- `## Do Not Re-Explain`
- `## Next Episode Handoff Notes`

The memory should be compact. It should not become a second research database. If the file grows beyond a few thousand words, the right fix is to compress it or introduce the callback index, not to pass more text.

## Episode Context Format

`episodes/<group-id>/course_context.md` should use stable headings:

- `# Course Context For <group-id>`
- `## Prior Course Grounding`
- `## Already Covered`
- `## Current Episode Scope`
- `## Transition Into This Episode`
- `## Production Constraint`
- `## Source Priority`

The source priority rule is important: current research records and current packets are factual sources; prior course context is continuity guidance.

## Group 003 Design

Group 003 covers:

- 11. Quantum theories
- 12. Integrated information theory
- 13. Panpsychisms
- 14. Monisms
- 15. Dualisms

The context should say that group 001 established the basic problem framing and group 002 established the fundamentality, identity, materialism, and non-reductive physicalism setup. Group 003 moves into theories that challenge, extend, or compete with the physicalist frame. It should avoid re-explaining Mary, zombies, the hard problem from scratch, or the full materialism setup, while keeping epistemic-status tagging sharp because the cluster mixes empirical, formal, speculative, and metaphysical theories.

## Validation

Phase 1 is valid when:

- `uv run python -m consciousness_pipeline.cli write-context --episode-id group-003` creates `episodes/group-003/course_context.md`.
- The generated context includes prior grounding, current section titles, transition guidance, production constraints, and source priority.
- `jobs/source-scripts.jsonl` includes `episodes/<group-id>/course_context.md` in source-script job `input_paths`.
- The source-dossier prompt still includes the required `## Course Continuity Grounding` scaffold.
- Ruff, Pyright, and unit tests pass.

