# Episode Quality Improvement Plan

Date: 2026-05-21

Implementation status: active pass implemented for pipeline and docs. Remaining work is human listening
decisions for rendered audio.

## Goal

Improve the first six completed consciousness podcast episodes against the course contract without
weakening the pipeline's epistemic discipline. The course should remain rigorous and non-overclaiming, but
future episodes should become more vivid, easier to navigate, and easier to evaluate after NotebookLM audio
generation.

## Current Baseline

Completed local continuity:

- accepted source dossiers for `group-001` through `group-006`
- accepted episode capsules for `group-001` through `group-006`
- source-dossier review files for `group-001` through `group-006`
- listener-facing titles and one-sentence promises in `course/listener-facing-titles.md`
- callback index with 36 callback concepts
- NotebookLM bundles for all six top-level episodes
- post-audio review checklists for audio-ready/review-pending groups 001-006

Operational gaps:

- `group-001`, `group-002`, and `group-003` have captured NotebookLM URLs and generated Deep Dive audio, but still need human listening decisions
- audio-ready/review-pending groups 001-006 have review checklists, but each still needs a human listening decision
- `group-003` NotebookLM source names appear with `.txt` suffixes rather than the local `.md` bundle names, so its listening pass should watch for any legacy handoff distortion
- accepted source dossiers for groups 001-006 predate the compact verdict matrix

## Phase 1: Status And Review Hygiene

1. Done: reconciled `course/production-status.csv` against the actual files and known NotebookLM notebooks.
2. Done: added retrospective manual review artifacts for `group-001`, `group-002`, `group-003`, and
   `group-006`.
3. Done: record that `group-001`, `group-002`, and `group-003` have entered the NotebookLM audio request path.
4. Done for `group-001`: captured the NotebookLM URL, verified the six-file bundle, and found Deep Dive audio available.
5. Done for `group-002`: verified the six-file bundle and found Deep Dive audio available.
6. Done for `group-003`: captured the NotebookLM URL, verified six expected source titles, and found Deep Dive audio available; note that NotebookLM displays the sources with `.txt` suffixes.
7. Keep the review standard from `group-004` and `group-005`: factual source material, no dialogue, no
   banter, no untagged speculative claims, clear source traceability.

## Phase 2: Listener-Facing Episode Framing

Done: add a listener-facing title and one-sentence promise for each top-level episode. Keep generated internal
IDs stable, but expose better labels in docs and future handoff notes.

Suggested working titles:

| Episode | Working title |
| --- | --- |
| `group-001` | The Hard Problem And The Map Legend |
| `group-002` | Brain Dependence, Identity, And The Physicalist Fork |
| `group-003` | Big Ontologies Under Pressure |
| `group-004` | Idealism, Anomalies, And The Challenge Arguments |
| `group-005` | Consequences Under Uncertainty |
| `group-006` | Disciplined Pluralism After The Landscape |

Implementation choice: keep generated manifests unchanged and maintain a separate listener-facing title table
in `course/listener-facing-titles.md`.

## Phase 3: Dossier Template Upgrade

Done for future jobs: update the source-dossier prompt so each new episode includes a compact verdict matrix:

| Axis | Required answer |
| --- | --- |
| Target | What kind of consciousness is at issue? |
| Ontology | What does the theory say consciousness is? |
| Bridge relation | Identity, realization, constitution, grounding, emergence, illusion, or other |
| Strongest evidence | Best source-backed support |
| Strongest objection | Best source-backed pressure point |
| What would change our mind | A concrete test, argument, or discovery |
| What not to infer | The most tempting overclaim to block |

This is added to future dossiers first. Backfilling groups 001-006 remains lower priority than preserving
accepted source dossiers unless a concrete factual or handoff problem is found.

## Phase 4: Post-Audio QA

Done for audio-ready episodes: create a lightweight post-audio QA artifact for each NotebookLM episode:

- `episodes/<group-id>/audio_review.md`
- fields: audio URL, completion status, listener clarity, pacing, overclaim risk, false-balance risk,
  missed concepts, memorable takeaway, and recommended fixes
- mark whether the audio should be accepted, regenerated with a revised prompt, or left as-is

This QA should evaluate the rendered audio, not the source dossier. It should not replace `review.json`,
which is a source-dossier acceptance artifact.

## Phase 5: Memory And Context Discipline

Keep the current compactness gains:

- new capsules should stay close to 6-10 durable concepts, 4-7 callbacks, and 5-8 open tensions
- ordinary `course_context.md` files should stay under about 1,500 words
- synthesis episodes may be longer, but the reason should be explicit in review notes
- callback families and tags should continue to support deduplication

Do not regenerate or rely on `course/course_memory.md`.

## Acceptance Criteria

This improvement pass is complete when:

- production status accurately distinguishes accepted dossiers, NotebookLM requests, and ready audio: done
- every accepted top-level episode has a source-dossier review artifact: done
- listener-facing titles exist for groups 001-006: done
- future source-dossier jobs include the verdict matrix: done
- audio-ready episodes have post-audio QA artifacts: done
- README and course docs describe the current state rather than historical implementation intent: done
- audio-ready episodes have human listening decisions: pending

## Non-Goals

- Do not rewrite accepted source dossiers unless a concrete factual or handoff problem is found.
- Do not collapse NotebookLM bundles into one source.
- Do not adjudicate the correct theory of consciousness.
- Do not let polish weaken epistemic status labels or bridge-relation discipline.
