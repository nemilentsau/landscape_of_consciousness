# Course Continuity Artifacts

`course_contract.md` is static production guidance for every episode. It defines the course purpose,
epistemic discipline, comparison axes, and NotebookLM handoff rules.

Accepted episode continuity is not stored in a regenerated global memory file. After a reviewed dossier is
accepted, `accept-episode` writes one immutable capsule to `course/episode_capsules/<group-id>.json` and
rebuilds `callback_index.json` from accepted capsules.

`course_memory.md` is deprecated and removed from the active pipeline. Later episode context packs are
generated from the contract, recent capsules, and relevant callback-index entries.
