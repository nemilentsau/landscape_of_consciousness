# Memory Pruning Plan

## Purpose

The course memory system is working, but the first five accepted episodes show early signs of memory bloat. Episode capsules and rendered course contexts are becoming recap-heavy instead of serving as compact guidance for future production jobs.

This plan keeps continuity useful while preventing future episode prompts from carrying too much prior-course material.

## Current Observations

Accepted capsule size is growing quickly:

- `group-001`: about 9.9 KB
- `group-002`: about 10.8 KB
- `group-003`: about 12.9 KB
- `group-004`: about 21.1 KB
- `group-005`: about 34.3 KB

Rendered course context is also expanding:

- `group-003`: about 2,291 words
- `group-004`: about 2,244 words
- `group-005`: about 4,648 words

The main cause is that selected prior capsules are rendered with full durable-concept summaries, broad recurring distinctions, all selected callbacks, all do-not-reexplain items, and all open tensions. This is accurate but too expansive for long-term use.

## Problems To Solve

### 1. Capsule Bloat

`group-005` has 20 durable concepts, 11 callbacks, and 13 open tensions. That is too much durable memory for a single episode unless the episode is intentionally acting as a course-level synthesis.

Future capsules should preserve only what will likely matter downstream.

### 2. Callback Duplication

Several callbacks now overlap semantically:

- epistemic tagging and false-balance warnings
- bridge-relation discipline
- identity criteria for AI and uploading
- report-versus-experience cautions
- brain-dependence constraints

These should become canonical callback families instead of accumulating as near-duplicate concept labels.

### 3. Context Rendering Too Much Prior Material

Current rendering includes large chunks of selected prior capsules. Future episode contexts should be selective, not archival.

The source dossiers and capsules remain the archival layer. `course_context.md` should be the working-memory layer.

### 4. Mixed Era Artifacts

Groups 001-003 were accepted before the review-gate workflow existed. Groups 004-005 have explicit `review.json` files.

This is not blocking, but the status and memory-management workflow should account for it.

## Target Memory Shape

### Episode Capsule Budget

Use these defaults for new accepted capsules:

- 6-10 durable concepts
- 4-7 recurring distinctions
- 4-7 do-not-reexplain items
- 5-8 open tensions
- 4-7 callbacks

Allow exceptions only for synthesis episodes, and mark them explicitly in the review notes.

### Callback Canonicalization

Introduce provisional callback families. These are a seed taxonomy for grouping recurring memory warnings, not a closed ontology. The implementation should make it easy to add, remove, rename, split, or consolidate families as later episodes reveal what actually recurs.

Candidate seed families:

- `target_phenomenon_discipline`
- `bridge_relation_required`
- `epistemic_false_balance`
- `brain_dependence_constraint`
- `report_not_experience`
- `ai_fluency_not_consciousness`
- `identity_continuity_required`
- `anomalous_claims_conditional`
- `formalism_not_confirmation`
- `metaphysical_breadth_not_explanation`

Each callback can still have episode-specific wording, but it should map to one canonical family.

At first, callback families should be advisory rather than enforced. Treat them as grouping hints for memory selection and de-duplication, not as a strict enum. The course should periodically consolidate families after enough new episodes exist to show real usage patterns.

Callbacks may also carry optional tags for topic-level selection. For example:

```json
{
  "concept": "Use architecture-sensitive AI indicators rather than fluency or self-report",
  "family": "ai_fluency_not_consciousness",
  "tags": ["ai", "measurement", "phenomenal_consciousness", "moral_status"],
  "summary": "...",
  "source_path": "...",
  "useful_for_future_sections": ["AI consciousness", "machine consciousness", "moral status"]
}
```

The family groups the callback with related memory rules. Tags help select callbacks for specific future episode topics.

### Course Context Budget

Rendered `course_context.md` should target:

- 1-2 sentence thesis per selected prior episode
- selected callbacks only, preferably 3-6 total
- top 3 do-not-reexplain rules
- top 3-5 open tensions
- no full durable-concept dump unless explicitly requested

For ordinary episodes, keep course context under about 1,500 words. For synthesis/reflection episodes, keep it under about 2,500 words unless a review explicitly approves more.

## Implementation Steps

### Step 1. Add Memory Budgets To Capsule Generation

Update the capsule-generation prompt in `consciousness_pipeline/agent_jobs.py` so capsule jobs explicitly prefer compact durable memory.

The prompt should say:

- extract only durable continuity likely to matter in future episodes
- avoid restating every section summary
- merge overlapping concepts
- prefer fewer, sharper callbacks
- mark synthesis exceptions explicitly

### Step 2. Add Optional Callback Family And Tags

Extend the episode capsule schema with optional callback fields:

```json
"family": {"type": "string"},
"tags": {"type": "array", "items": {"type": "string"}}
```

These fields should be allowed on callback entries but not required at first. This keeps old capsules valid while enabling gradual grouping and topic-aware selection.

Do not validate `family` against a fixed enum in the first implementation. Keep it free-form and document the known seed families in this plan or a later small registry file. Add enum validation only if the family set becomes stable and the added strictness clearly helps.

### Step 3. Canonicalize The Callback Index

Update `build_callback_index` so it exposes callback `family` and `tags` when present.

Initial behavior can remain backward-compatible:

- if `family` exists, include it in callback index entries
- if `tags` exist, include them in callback index entries
- if neither exists, continue using `concept` and `useful_for_future_sections`

Later, context selection can prefer diversity across families unless the selected episode needs multiple callbacks from the same family. It should avoid near-duplicates, not mechanically enforce one callback per family.

After several more episodes, review family usage and consolidate obvious duplicates. If a family is renamed or merged, preserve backward compatibility by supporting old family names until affected capsules are regenerated.

### Step 4. Compact Course Context Rendering

Change `render_episode_course_context` so selected prior capsules render as compact summaries:

- episode id and title
- thesis shortened or used as-is if already short
- selection reason
- at most three durable-concept names, without full summaries

Move full capsule rendering behind an explicit option for debugging or review.

### Step 5. Rank Do-Not-Reexplain And Open Tensions

Instead of including all inherited items, select the most relevant ones.

Short-term rule:

- include items from explicitly selected callbacks first
- include items whose text overlaps the current manifest search text
- include recent episode items as tie-breakers
- cap the final list

Long-term rule:

- have the context-selection job choose these directly

### Step 6. Backfill Group 005 Compact Capsule

Create a compact replacement or companion for `group-005` after the renderer supports tighter memory.

Recommended target:

- reduce durable concepts from 20 to about 10
- reduce open tensions from 13 to about 7
- keep callbacks focused on implication discipline, AI consciousness, uploading identity, survival evidence, meaning/value distinction, and false-balance control

Do not delete the accepted source dossier. The dossier remains the factual archive.

### Step 7. Use Group 006 As A Stress Test

`group-006` is `Reflections`, so it is a high-risk episode for overusing memory.

For group-006 context selection, prefer:

- `group-005` as recent grounding
- one callback from `group-001` on target phenomenon
- one callback from `group-002` on bridge relation or identity
- one callback from `group-004` on false balance or anomaly discipline

Avoid importing full prior capsules unless the reflection section explicitly requires it.

## Acceptance Criteria

The memory-pruning work is done when:

- new capsule jobs produce compact capsules by default
- course contexts for ordinary episodes stay under about 1,500 words
- selected callbacks are not near-duplicates of the same warning
- callback index entries can expose provisional families and tags
- context selection can use families as advisory de-duplication hints without requiring a fixed taxonomy
- group-006 context is concise despite having five accepted prior episodes available
- all quality gates pass:

```bash
uv run ruff check .
uv run pyright
uv run python -m unittest discover -s tests -v
```

## Non-Goals

- Do not collapse NotebookLM bundles.
- Do not remove accepted dossiers.
- Do not recreate `course/course_memory.md`.
- Do not treat prior continuity as evidence for current episode claims.
- Do not make the memory layer so terse that future episodes lose course identity.

## Guiding Principle

The durable archive can be rich. The working memory must be selective.
