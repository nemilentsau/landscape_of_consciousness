import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.course.callback_index import write_callback_index
from consciousness_pipeline.quality.evaluations import evaluate_episode


def _research_record(section_id: str) -> dict[str, object]:
    return {
        "section_id": section_id,
        "opening_question": f"What does section {section_id} put at stake?",
        "core_claim": f"Section {section_id} advances a substantive research claim with enough detail.",
        "strongest_case": f"Section {section_id} has a strongest case grounded in named academic sources.",
        "best_objections": f"Section {section_id} also has objections, boundary conditions, and limits.",
        "credibility": "Active debate with mainstream and dissenting sources clearly separated.",
        "listener_hooks": ["A concrete listener hook."],
        "sources": [
            {"kind": "primary", "title": "A landscape of consciousness", "url": "", "citation": "Kuhn 2024"},
            {"kind": "review", "title": "External review", "url": "https://example.com", "citation": "Example 2024"},
        ],
    }


def _source_markdown(title: str) -> str:
    body = " ".join(["substantive source material"] * 80)
    return f"""# {title}

## Kuhn Review Anchor
Section anchor.

## Research Question
What is at stake?

## Core Claim
{body}

## Strongest Case
{body}

## Best Objections And Limits
{body}

## Credibility / Epistemic Status
{body}

## Sources
- primary: Kuhn 2024 A landscape of consciousness
- review: Example 2024 External review https://example.com
"""


def _dossier_markdown(*, include_verdict_matrix: bool = True) -> str:
    body = " ".join(["substantive dossier material"] * 220)
    verdict_matrix = (
        """## Verdict Matrix

| Target | Ontology | Bridge | Evidence | Objection | Change mind | Do not infer |
| --- | --- | --- | --- | --- | --- | --- |
| Phenomenality | Open | Disputed | Evidence | Objection | Better bridge | Premature reduction |

"""
        if include_verdict_matrix
        else ""
    )
    return f"""## Episode Metadata

- Episode group: `group-001`
- Sections covered: Hard problem; Initial thoughts.

## Course Continuity Grounding

{body}

{verdict_matrix}\
## Source Notes And Local Input Paths

Local inputs used: `data/research/1.json`, `data/research/2.json`.
"""


def _write_audio_status(root: Path, audio_status: str) -> None:
    status_path = root / "course" / "production-status.csv"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        "group_id,section_id,packet_slug,research_status,script_status,notebooklm_status,notebook_url,"
        "audio_status,message\n"
        f"group-001,1,01-hard-problem,researched,source_script_ready,notebooklm_bundle_ready,"
        f"https://example.com/notebook,{audio_status},ready\n",
        encoding="utf-8",
    )


def write_episode_root(root: Path, *, bloated: bool = False) -> None:
    episode_dir = root / "episodes" / "group-001"
    episode_dir.mkdir(parents=True)
    (episode_dir / "manifest.json").write_text(
        json.dumps(
            {
                "episode_id": "group-001",
                "title": "Top-level sections Part 1",
                "episode_question": "What is the target?",
                "section_ids": ["1", "2"],
                "sections": [
                    {"section_id": "1", "title": "Hard problem", "pages": "1-2"},
                    {"section_id": "2", "title": "Initial thoughts", "pages": "3-4"},
                ],
            }
        ),
        encoding="utf-8",
    )
    context_words = 1600 if bloated else 120
    (episode_dir / "course_context.md").write_text("context " * context_words, encoding="utf-8")
    bundle_dir = episode_dir / "notebooklm_bundle"
    sources_dir = bundle_dir / "sources"
    sources_dir.mkdir(parents=True)
    dossier = _dossier_markdown()
    (bundle_dir / "research_dossier.md").write_text(dossier, encoding="utf-8")
    (episode_dir / "script.json").write_text(
        json.dumps(
            {
                "episode_id": "group-001",
                "title": "Top-level sections Part 1",
                "episode_question": "What is the target?",
                "duration_target": "long_form",
                "research_dossier_markdown": dossier,
                "citations": ["Kuhn 2024", "Example 2024"],
                "missing_inputs": [],
            }
        ),
        encoding="utf-8",
    )
    (sources_dir / "01-hard-problem.md").write_text(_source_markdown("Source 1"), encoding="utf-8")
    (sources_dir / "02-initial-thoughts.md").write_text(_source_markdown("Source 2"), encoding="utf-8")
    research_dir = root / "data" / "research"
    research_dir.mkdir(parents=True)
    (research_dir / "1.json").write_text(json.dumps(_research_record("1")), encoding="utf-8")
    (research_dir / "2.json").write_text(json.dumps(_research_record("2")), encoding="utf-8")
    capsule_dir = root / "course" / "episode_capsules"
    capsule_dir.mkdir(parents=True)
    concept_count = 11 if bloated else 2
    callbacks = [
        {
            "concept": "target discipline",
            "family": "target_phenomenon_discipline",
            "tags": ["phenomenal_consciousness"],
            "summary": "Keep the target phenomenon explicit.",
            "source_path": "episodes/group-001/notebooklm_bundle/research_dossier.md",
            "useful_for_future_sections": ["all future sections"],
        }
    ]
    (capsule_dir / "group-001.json").write_text(
        json.dumps(
            {
                "schema_version": "episode_capsule_v1",
                "episode_id": "group-001",
                "title": "Top-level sections Part 1",
                "accepted_dossier_path": "episodes/group-001/notebooklm_bundle/research_dossier.md",
                "section_ids": ["1", "2"],
                "thesis": "A compact thesis.",
                "durable_concepts": [
                    {
                        "concept": f"concept-{index}",
                        "summary": "Durable summary.",
                        "source_path": "episodes/group-001/notebooklm_bundle/research_dossier.md",
                    }
                    for index in range(concept_count)
                ],
                "recurring_distinctions": ["target vs proxy"],
                "do_not_reexplain": ["Do not reteach the hard problem."],
                "open_tensions": ["The bridge remains unsettled."],
                "callbacks": callbacks,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    write_callback_index(capsule_dir, root / "course" / "callback_index.json", root=root)


class EpisodeEvaluationTest(unittest.TestCase):
    def test_evaluate_episode_accepts_clean_episode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root)

            report = evaluate_episode(root, "group-001")

            self.assertTrue(report["ok"])
            self.assertEqual(report["summary"], {"errors": 0, "warnings": 0, "issues": 0})

    def test_evaluate_episode_warns_on_memory_bloat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root, bloated=True)

            report = evaluate_episode(root, "group-001")

            self.assertTrue(report["ok"])
            check_ids = {issue["check_id"] for issue in report["issues"]}  # type: ignore[index]
            self.assertIn("context_word_budget", check_ids)
            self.assertIn("capsule_durable_concepts_budget", check_ids)

    def test_evaluate_episode_flags_bundle_source_count_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root)
            (root / "episodes" / "group-001" / "notebooklm_bundle" / "sources" / "02-initial-thoughts.md").unlink()

            report = evaluate_episode(root, "group-001", stage="bundle")

            self.assertFalse(report["ok"])
            check_ids = {issue["check_id"] for issue in report["issues"]}  # type: ignore[index]
            self.assertIn("bundle_source_count", check_ids)

    def test_evaluate_episode_has_first_class_research_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root)
            (root / "data" / "research" / "1.json").write_text(
                json.dumps(
                    {
                        "section_id": "1",
                        "opening_question": "What is missing?",
                        "core_claim": "Research incomplete: use Kuhn's section text as the starting point.",
                        "strongest_case": "Research incomplete",
                        "best_objections": "Research incomplete",
                        "credibility": "Research incomplete",
                        "listener_hooks": [],
                        "sources": [],
                    }
                ),
                encoding="utf-8",
            )

            report = evaluate_episode(root, "group-001", stage="research")

            self.assertFalse(report["ok"])
            check_ids = {issue["check_id"] for issue in report["issues"]}  # type: ignore[index]
            self.assertIn("research_field_incomplete", check_ids)
            self.assertIn("research_sources_missing", check_ids)
            self.assertNotIn("script_missing", check_ids)

    def test_evaluate_episode_flags_performed_dialogue_dossiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root)
            dialogue = (
                "## Episode Metadata\n\n"
                "HOST: Welcome back.\n\n"
                "## Course Continuity Grounding\n\n"
                "## Source Notes And Local Input Paths\n"
            )
            script_path = root / "episodes" / "group-001" / "script.json"
            script = json.loads(script_path.read_text(encoding="utf-8"))
            script["research_dossier_markdown"] = dialogue
            script_path.write_text(json.dumps(script), encoding="utf-8")
            (root / "episodes" / "group-001" / "notebooklm_bundle" / "research_dossier.md").write_text(
                dialogue,
                encoding="utf-8",
            )

            report = evaluate_episode(root, "group-001", stage="dossier")

            self.assertFalse(report["ok"])
            check_ids = {issue["check_id"] for issue in report["issues"]}  # type: ignore[index]
            self.assertIn("script_performed_dialogue", check_ids)
            self.assertIn("dossier_performed_dialogue", check_ids)

    def test_evaluate_episode_warns_when_dossier_has_no_verdict_matrix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root)
            dossier = _dossier_markdown(include_verdict_matrix=False)
            (root / "episodes" / "group-001" / "notebooklm_bundle" / "research_dossier.md").write_text(
                dossier,
                encoding="utf-8",
            )
            script_path = root / "episodes" / "group-001" / "script.json"
            script = json.loads(script_path.read_text(encoding="utf-8"))
            script["research_dossier_markdown"] = dossier
            script_path.write_text(json.dumps(script), encoding="utf-8")

            report = evaluate_episode(root, "group-001", stage="dossier")

            self.assertTrue(report["ok"])
            check_ids = {issue["check_id"] for issue in report["issues"]}  # type: ignore[index]
            self.assertIn("dossier_verdict_matrix_missing", check_ids)

    def test_evaluate_episode_audio_stage_warns_when_episode_has_no_status_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root)

            report = evaluate_episode(root, "group-001", stage="audio")

            self.assertTrue(report["ok"])
            check_ids = {issue["check_id"] for issue in report["issues"]}  # type: ignore[index]
            self.assertIn("audio_status_missing", check_ids)

    def test_evaluate_episode_audio_stage_warns_when_audio_is_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root)
            _write_audio_status(root, "audio_requested")

            report = evaluate_episode(root, "group-001", stage="audio")

            self.assertTrue(report["ok"])
            check_ids = {issue["check_id"] for issue in report["issues"]}  # type: ignore[index]
            self.assertIn("audio_not_ready", check_ids)

    def test_evaluate_episode_audio_stage_requires_review_for_audio_ready_episode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root)
            _write_audio_status(root, "audio_ready")

            report = evaluate_episode(root, "group-001", stage="audio")

            self.assertFalse(report["ok"])
            check_ids = {issue["check_id"] for issue in report["issues"]}  # type: ignore[index]
            self.assertIn("audio_review_missing", check_ids)

    def test_evaluate_episode_audio_stage_warns_on_pending_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root)
            _write_audio_status(root, "audio_ready")
            (root / "episodes" / "group-001" / "audio_review.md").write_text(
                "# Audio Review: group-001\n\nReview status: pending_human_listen\n\n## Decision\n\nPending.\n",
                encoding="utf-8",
            )

            report = evaluate_episode(root, "group-001", stage="audio")

            self.assertTrue(report["ok"])
            check_ids = {issue["check_id"] for issue in report["issues"]}  # type: ignore[index]
            self.assertIn("audio_review_pending", check_ids)

    def test_evaluate_episode_audio_stage_accepts_reviewed_audio_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root)
            _write_audio_status(root, "audio_accepted")
            (root / "episodes" / "group-001" / "audio_review.md").write_text(
                "# Audio Review: group-001\n\nReview status: accepted\n\n## Decision\n\nAccepted.\n",
                encoding="utf-8",
            )

            report = evaluate_episode(root, "group-001", stage="audio")

            self.assertTrue(report["ok"])
            check_ids = {issue["check_id"] for issue in report["issues"]}  # type: ignore[index]
            self.assertNotIn("audio_not_ready", check_ids)
            self.assertNotIn("audio_review_pending", check_ids)


if __name__ == "__main__":
    unittest.main()
