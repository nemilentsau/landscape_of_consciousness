import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.course_context import render_episode_course_context, write_episode_course_context


def manifest() -> dict[str, object]:
    return {
        "episode_id": "group-003",
        "title": "Top-level sections Part 3",
        "episode_question": "What is the strongest case for this cluster, and where does it break?",
        "sections": [
            {"section_id": "11", "title": "Quantum theories", "pages": "13-16"},
            {"section_id": "12", "title": "Integrated information theory", "pages": "16-20"},
            {"section_id": "13", "title": "Panpsychisms", "pages": "20-24"},
        ],
    }


def capsule(episode_id: str, concept: str) -> dict[str, object]:
    return {
        "schema_version": "episode_capsule_v1",
        "episode_id": episode_id,
        "title": f"{episode_id} title",
        "accepted_dossier_path": f"episodes/{episode_id}/notebooklm_bundle/research_dossier.md",
        "section_ids": ["1"],
        "thesis": f"{episode_id} thesis",
        "durable_concepts": [
            {"concept": concept, "summary": f"{concept} summary", "source_path": "course/test.md"}
        ],
        "recurring_distinctions": ["correlation vs explanation"],
        "do_not_reexplain": [f"{episode_id} do not reteach"],
        "open_tensions": [f"{episode_id} open tension"],
        "callbacks": [],
    }


class CourseContextTest(unittest.TestCase):
    def test_render_episode_course_context_uses_contract_capsules_and_callback_index(self):
        text = render_episode_course_context(
            manifest(),
            course_contract="# Consciousness Course Contract\n\nStatic rules.",
            prior_capsules=[capsule("group-001", "hard_problem"), capsule("group-002", "brain_dependence")],
            callback_index={
                "integrated_information_theory": [
                    {
                        "episode_id": "group-001",
                        "capsule_path": "course/episode_capsules/group-001.json",
                        "accepted_dossier_path": "episodes/group-001/notebooklm_bundle/research_dossier.md",
                        "source_path": "episodes/group-001/notebooklm_bundle/research_dossier.md",
                        "summary": "Compare formal measure claims against explanation.",
                        "useful_for_future_sections": ["Integrated information theory"],
                    }
                ]
            },
        )

        self.assertIn("# Course Context For group-003", text)
        self.assertIn("## Course Contract", text)
        self.assertIn("## Current Episode Scope", text)
        self.assertIn("## Selected Prior Grounding", text)
        self.assertIn("## Relevant Callbacks", text)
        self.assertIn("## Do Not Re-Explain", text)
        self.assertIn("## Open Tensions To Preserve", text)
        self.assertIn("## Source Priority", text)
        self.assertIn("Static rules.", text)
        self.assertIn("group-002 thesis", text)
        self.assertIn("Quantum theories", text)
        self.assertIn("Integrated information theory", text)
        self.assertIn("Compare formal measure claims", text)
        self.assertIn("current research records and packet inputs are factual sources", text)
        self.assertNotIn("## Prior Course Grounding", text)

    def test_write_episode_course_context_selects_recent_capsules_and_relevant_callbacks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            group_dir = root / "episodes" / "group-003"
            group_dir.mkdir(parents=True)
            (group_dir / "manifest.json").write_text(json.dumps(manifest()), encoding="utf-8")
            course_dir = root / "course"
            capsule_dir = course_dir / "episode_capsules"
            capsule_dir.mkdir(parents=True)
            (course_dir / "course_contract.md").write_text("# Contract\n\nDo rigorous continuity.", encoding="utf-8")
            for prior in (
                capsule("group-001", "hard_problem"),
                capsule("group-002", "brain_dependence"),
                capsule("group-004", "future_episode"),
            ):
                (capsule_dir / f"{prior['episode_id']}.json").write_text(json.dumps(prior), encoding="utf-8")
            (course_dir / "callback_index.json").write_text(
                json.dumps(
                    {
                        "integrated_information_theory": [
                            {
                                "episode_id": "group-001",
                                "capsule_path": "course/episode_capsules/group-001.json",
                                "accepted_dossier_path": "episodes/group-001/notebooklm_bundle/research_dossier.md",
                                "source_path": "episodes/group-001/notebooklm_bundle/research_dossier.md",
                                "summary": "Relevant IIT callback.",
                                "useful_for_future_sections": ["Integrated information theory"],
                            }
                        ],
                        "future_episode": [
                            {
                                "episode_id": "group-004",
                                "capsule_path": "course/episode_capsules/group-004.json",
                                "accepted_dossier_path": "episodes/group-004/notebooklm_bundle/research_dossier.md",
                                "source_path": "episodes/group-004/notebooklm_bundle/research_dossier.md",
                                "summary": "Should not be selected.",
                                "useful_for_future_sections": ["Reflections"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            output_path = write_episode_course_context(root, "group-003", recent_count=2)

            text = output_path.read_text(encoding="utf-8")
            self.assertIn("group-001 thesis", text)
            self.assertIn("group-002 thesis", text)
            self.assertNotIn("group-004 thesis", text)
            self.assertIn("Relevant IIT callback.", text)
            self.assertNotIn("Should not be selected.", text)


if __name__ == "__main__":
    unittest.main()
