import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.course.callback_index import build_callback_index, write_callback_index


def write_capsule(root: Path, episode_id: str, concept: str) -> Path:
    dossier = root / "episodes" / episode_id / "notebooklm_bundle" / "research_dossier.md"
    dossier.parent.mkdir(parents=True)
    dossier.write_text("# Accepted dossier\n", encoding="utf-8")
    capsule_path = root / "course" / "episode_capsules" / f"{episode_id}.json"
    capsule_path.parent.mkdir(parents=True, exist_ok=True)
    capsule_path.write_text(
        json.dumps(
            {
                "schema_version": "episode_capsule_v1",
                "episode_id": episode_id,
                "title": f"{episode_id} title",
                "accepted_dossier_path": f"episodes/{episode_id}/notebooklm_bundle/research_dossier.md",
                "section_ids": ["1"],
                "thesis": "A durable thesis.",
                "durable_concepts": [
                    {
                        "concept": concept,
                        "summary": f"{concept} durable summary",
                        "source_path": f"episodes/{episode_id}/notebooklm_bundle/research_dossier.md",
                    }
                ],
                "recurring_distinctions": [],
                "do_not_reexplain": [],
                "open_tensions": [],
                "callbacks": [
                    {
                        "concept": concept,
                        "family": "target_phenomenon_discipline",
                        "tags": ["phenomenal_consciousness", "course_memory"],
                        "summary": f"{concept} callback summary",
                        "source_path": f"episodes/{episode_id}/notebooklm_bundle/research_dossier.md",
                        "useful_for_future_sections": ["panpsychism"],
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return capsule_path


class CallbackIndexTest(unittest.TestCase):
    def test_build_callback_index_groups_callbacks_by_concept_with_traceable_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_capsule(root, "group-002", "hard_problem")
            write_capsule(root, "group-001", "phenomenal_consciousness")

            index = build_callback_index(root / "course" / "episode_capsules", root=root)

            self.assertEqual(list(index), ["hard_problem", "phenomenal_consciousness"])
            hard_problem = index["hard_problem"][0]
            self.assertEqual(hard_problem["episode_id"], "group-002")
            self.assertEqual(hard_problem["capsule_path"], "course/episode_capsules/group-002.json")
            self.assertEqual(
                hard_problem["accepted_dossier_path"],
                "episodes/group-002/notebooklm_bundle/research_dossier.md",
            )
            self.assertEqual(hard_problem["source_path"], "episodes/group-002/notebooklm_bundle/research_dossier.md")
            self.assertEqual(hard_problem["useful_for_future_sections"], ["panpsychism"])
            self.assertEqual(hard_problem["family"], "target_phenomenon_discipline")
            self.assertEqual(hard_problem["tags"], ["phenomenal_consciousness", "course_memory"])

    def test_write_callback_index_is_deterministic_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_capsule(root, "group-002", "hard_problem")
            output_path = root / "course" / "callback_index.json"

            write_callback_index(root / "course" / "episode_capsules", output_path, root=root)

            text = output_path.read_text(encoding="utf-8")
            self.assertTrue(text.endswith("\n"))
            self.assertEqual(json.loads(text), build_callback_index(root / "course" / "episode_capsules", root=root))


if __name__ == "__main__":
    unittest.main()
