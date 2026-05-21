# Course Continuity Artifacts

`course_contract.md` is static production guidance for every episode. It defines the course purpose,
epistemic discipline, comparison axes, and NotebookLM handoff rules.

Accepted episode continuity is not stored in a regenerated global memory file. After a reviewed dossier is
accepted, `accept-episode` writes one immutable capsule to `course/episode_capsules/<group-id>.json` and
rebuilds `callback_index.json` from accepted capsules.

`course_memory.md` is removed from the active pipeline. Later episode context packs are generated from the
contract, recent capsules, and relevant callback-index entries.

`listener-facing-titles.md` gives stable human-facing titles and promises for the first six orientation
episodes without changing generated internal ids.

## Current Accepted Continuity

As of 2026-05-21, accepted continuity exists for the six top-level orientation episodes:

| Episode | Listener title | Sections | Continuity | NotebookLM audio status |
| --- | --- | --- | --- | --- |
| `group-001` | The Hard Problem And The Map Legend | 1-5 | capsule accepted, review present | `not_started` |
| `group-002` | Brain Dependence, Identity, And The Physicalist Fork | 6-10 | capsule accepted, review present | `audio_requested` |
| `group-003` | Big Ontologies Under Pressure | 11-15 | capsule accepted, review present | `not_started` |
| `group-004` | Idealism, Anomalies, And The Challenge Arguments | 16-20 | capsule accepted, review present | `audio_ready` |
| `group-005` | Consequences Under Uncertainty | 21-25 | capsule accepted, review present | `audio_ready` |
| `group-006` | Disciplined Pluralism After The Landscape | 26 | capsule accepted, review present | `audio_ready` |

Use `production-status.csv` as the operational handoff ledger. It is not a replacement for the immutable
episode capsules or accepted source dossiers.

Use `episodes/<group-id>/audio_review.md` for rendered-audio QA. It is separate from `review.json`,
which evaluates the factual source dossier before continuity acceptance.
Audio review checklists exist for `group-004`, `group-005`, and `group-006`; all three are pending a
human listening decision.

## Active Improvement Roadmap

The active improvement roadmap is `docs/episode-quality-implementation-plan.md`.
