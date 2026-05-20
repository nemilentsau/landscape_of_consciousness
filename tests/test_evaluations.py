import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.callback_index import write_callback_index
from consciousness_pipeline.evaluations import evaluate_episode


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
    (bundle_dir / "research_dossier.md").write_text("# Dossier\n", encoding="utf-8")
    (sources_dir / "01-hard-problem.md").write_text("# Source 1\n", encoding="utf-8")
    (sources_dir / "02-initial-thoughts.md").write_text("# Source 2\n", encoding="utf-8")
    capsule_dir = root / "course" / "episode_capsules"
    capsule_dir.mkdir(parents=True)
    concept_count = 11 if bloated else 2
    callbacks = [
        {
            "concept": "target discipline",
            "summary": "Keep the target phenomenon explicit.",
            "source_path": "episodes/group-001/notebooklm_bundle/research_dossier.md",
            "useful_for_future_sections": ["all future sections"],
        }
    ]
    if not bloated:
        callbacks[0]["family"] = "target_phenomenon_discipline"
        callbacks[0]["tags"] = ["phenomenal_consciousness"]
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

    def test_evaluate_episode_warns_on_memory_bloat_and_missing_callback_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root, bloated=True)

            report = evaluate_episode(root, "group-001")

            self.assertTrue(report["ok"])
            check_ids = {issue["check_id"] for issue in report["issues"]}  # type: ignore[index]
            self.assertIn("context_word_budget", check_ids)
            self.assertIn("capsule_durable_concepts_budget", check_ids)
            self.assertIn("callback_family_missing", check_ids)
            self.assertIn("callback_tags_missing", check_ids)

    def test_evaluate_episode_flags_bundle_source_count_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_episode_root(root)
            (root / "episodes" / "group-001" / "notebooklm_bundle" / "sources" / "02-initial-thoughts.md").unlink()

            report = evaluate_episode(root, "group-001", stage="bundle")

            self.assertFalse(report["ok"])
            check_ids = {issue["check_id"] for issue in report["issues"]}  # type: ignore[index]
            self.assertIn("bundle_source_count", check_ids)


if __name__ == "__main__":
    unittest.main()

