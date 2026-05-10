import csv
import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.course import group_sections, write_course_artifacts
from consciousness_pipeline.models import Section


def make_section(section_id, title, parent="Materialism theories"):
    return Section(
        section_id=section_id,
        title=title,
        level=3,
        start_page=20,
        end_page=21,
        taxonomy_path=[parent, "Neurobiological theories", title],
        text=title,
        slug=section_id.replace(".", "-") + "-" + title.lower().replace(" ", "-"),
    )


class CourseGenerationTest(unittest.TestCase):
    def test_group_sections_keeps_groups_small(self):
        sections = [make_section(f"9.2.{index}", f"Theory {index}") for index in range(1, 7)]
        groups = group_sections(sections, max_group_size=5)
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups[0]["packet_slugs"]), 5)
        self.assertEqual(len(groups[1]["packet_slugs"]), 1)

    def test_write_course_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            sections = [make_section("9.2.3", "Global workspace theory")]
            write_course_artifacts(sections, output_dir)

            index = (output_dir / "exhaustive-index.md").read_text(encoding="utf-8")
            groups = json.loads((output_dir / "notebook-groups.json").read_text(encoding="utf-8"))
            with (output_dir / "production-status.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertIn("Global workspace theory", index)
            self.assertEqual(groups[0]["audio_format"], "Debate")
            self.assertEqual(groups[0]["audio_length"], "Longer")
            self.assertEqual(rows[0]["status"], "packet_ready")


if __name__ == "__main__":
    unittest.main()
