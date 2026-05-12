import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.course_context import (
    DEFAULT_COURSE_MEMORY,
    render_episode_course_context,
    write_initial_course_memory,
)


class CourseContextTest(unittest.TestCase):
    def test_write_initial_course_memory_records_durable_prior_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "course" / "course_memory.md"

            write_initial_course_memory(path)

            text = path.read_text(encoding="utf-8")
            self.assertEqual(text, DEFAULT_COURSE_MEMORY)
            self.assertIn("## Durable Concepts Introduced", text)
            self.assertIn("Group 001", text)
            self.assertIn("Group 002", text)
            self.assertIn("## Do Not Re-Explain", text)

    def test_render_episode_course_context_uses_memory_and_current_manifest(self):
        manifest = {
            "episode_id": "group-003",
            "title": "Top-level sections Part 3",
            "episode_question": "What is the strongest case for this cluster, and where does it break?",
            "sections": [
                {"section_id": "11", "title": "Quantum theories", "pages": "13-16"},
                {"section_id": "12", "title": "Integrated information theory", "pages": "16-20"},
                {"section_id": "13", "title": "Panpsychisms", "pages": "20-24"},
                {"section_id": "14", "title": "Monisms", "pages": "24-26"},
                {"section_id": "15", "title": "Dualisms", "pages": "26-30"},
            ],
        }

        text = render_episode_course_context(manifest, DEFAULT_COURSE_MEMORY)

        self.assertIn("# Course Context For group-003", text)
        self.assertIn("## Prior Course Grounding", text)
        self.assertIn("## Already Covered", text)
        self.assertIn("## Current Episode Scope", text)
        self.assertIn("Quantum theories", text)
        self.assertIn("Integrated information theory", text)
        self.assertIn("Panpsychisms", text)
        self.assertIn("Monisms", text)
        self.assertIn("Dualisms", text)
        self.assertIn("Group 003 moves into theories", text)
        self.assertIn("current research records and current packets are factual sources", text)

    def test_context_renderer_accepts_manifest_json_from_disk_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "episodes" / "group-003" / "manifest.json"
            memory_path = root / "course" / "course_memory.md"
            manifest_path.parent.mkdir(parents=True)
            memory_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "episode_id": "group-003",
                        "title": "Top-level sections Part 3",
                        "episode_question": "What is the strongest case for this cluster, and where does it break?",
                        "sections": [{"section_id": "11", "title": "Quantum theories", "pages": "13-16"}],
                    }
                ),
                encoding="utf-8",
            )
            memory_path.write_text(DEFAULT_COURSE_MEMORY, encoding="utf-8")

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            text = render_episode_course_context(manifest, memory_path.read_text(encoding="utf-8"))

            self.assertIn("group-003", text)
            self.assertIn("Quantum theories", text)


if __name__ == "__main__":
    unittest.main()
