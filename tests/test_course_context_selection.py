import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.course.context_selection import (
    CourseContextSelectionValidationError,
    validate_course_context_selection,
    write_course_context_selection_schema,
)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def capsule(episode_id: str) -> dict[str, object]:
    return {
        "schema_version": "episode_capsule_v1",
        "episode_id": episode_id,
        "title": f"{episode_id} title",
        "accepted_dossier_path": f"episodes/{episode_id}/notebooklm_bundle/research_dossier.md",
        "section_ids": ["1"],
        "thesis": f"{episode_id} thesis",
        "durable_concepts": [
            {
                "concept": "identity criteria",
                "summary": "Ask what preserves the subject.",
                "source_path": f"episodes/{episode_id}/notebooklm_bundle/research_dossier.md",
            }
        ],
        "recurring_distinctions": ["phenomenal vs access consciousness"],
        "do_not_reexplain": ["Do not restart the hard problem."],
        "open_tensions": ["Whether functional continuity preserves subject identity."],
        "callbacks": [],
    }


class CourseContextSelectionTest(unittest.TestCase):
    def test_validate_selection_requires_callbacks_to_exist_in_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dossier_path = root / "episodes" / "group-002" / "notebooklm_bundle" / "research_dossier.md"
            dossier_path.parent.mkdir(parents=True)
            dossier_path.write_text("Accepted dossier.", encoding="utf-8")
            write_json(root / "course" / "episode_capsules" / "group-002.json", capsule("group-002"))
            write_json(
                root / "course" / "callback_index.json",
                {
                    "machine_personhood_bridge": [
                        {
                            "episode_id": "group-002",
                            "capsule_path": "course/episode_capsules/group-002.json",
                            "accepted_dossier_path": "episodes/group-002/notebooklm_bundle/research_dossier.md",
                            "source_path": "episodes/group-002/notebooklm_bundle/research_dossier.md",
                            "summary": "Uploading claims need explicit identity criteria.",
                            "useful_for_future_sections": ["Synthetic minds"],
                        }
                    ]
                },
            )
            selection = {
                "schema_version": "course_context_selection_v1",
                "episode_id": "group-005",
                "selected_capsules": [
                    {
                        "episode_id": "group-002",
                        "selection_type": "relevant",
                        "reason": "Identity criteria constrain AI and upload sections.",
                    }
                ],
                "selected_callbacks": [
                    {
                        "concept": "machine_personhood_bridge",
                        "episode_id": "group-002",
                        "capsule_path": "course/episode_capsules/group-002.json",
                        "source_path": "episodes/group-002/notebooklm_bundle/research_dossier.md",
                        "reason": "Episode 5 asks whether artificial or uploaded systems preserve consciousness.",
                    }
                ],
                "rejected_near_misses": [],
            }

            validate_course_context_selection(selection, root=root)

            selection["selected_callbacks"][0]["source_path"] = "episodes/group-002/made-up.md"
            with self.assertRaises(CourseContextSelectionValidationError) as context:
                validate_course_context_selection(selection, root=root)
            self.assertIn("does not match callback_index", str(context.exception))

    def test_write_selection_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "schemas" / "course-context-selection.schema.json"

            write_course_context_selection_schema(path)

            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(schema["properties"]["schema_version"]["const"], "course_context_selection_v1")
            self.assertIn("selected_callbacks", schema["required"])
            near_miss_items = schema["properties"]["rejected_near_misses"]["items"]
            self.assertEqual(set(near_miss_items["required"]), set(near_miss_items["properties"]))


if __name__ == "__main__":
    unittest.main()
