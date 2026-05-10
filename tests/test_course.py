import csv
import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.course import group_sections, write_course_artifacts, write_episode_artifacts
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

    def test_group_sections_uses_stable_bucket_for_top_level_sections(self):
        sections = [
            make_section("1", "Introduction"),
            make_section("2", "Definitions"),
        ]
        sections = [
            Section(
                section_id=section.section_id,
                title=section.title,
                level=section.level,
                start_page=section.start_page,
                end_page=section.end_page,
                taxonomy_path=[section.title],
                text=section.text,
                slug=section.slug,
            )
            for section in sections
        ]

        groups = group_sections(sections)

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["title"], "Top-level sections")
        self.assertEqual(groups[0]["packet_slugs"], [section.slug for section in sections])

    def test_write_course_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            sections = [make_section("9.2.3", "Global workspace theory")]
            write_course_artifacts(sections, output_dir)

            index = (output_dir / "exhaustive-index.md").read_text(encoding="utf-8")
            groups = json.loads((output_dir / "episode-map.json").read_text(encoding="utf-8"))
            group_markdown = (output_dir / "episode-map.md").read_text(encoding="utf-8")
            with (output_dir / "production-status.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertIn("Global workspace theory", index)
            self.assertEqual(groups[0]["audio_profile"]["format"], "Deep Dive")
            self.assertEqual(groups[0]["audio_profile"]["length"], "Long")
            self.assertIn("Podcast Episode Map", group_markdown)
            self.assertEqual(rows[0]["research_status"], "research_queued")
            self.assertEqual(rows[0]["script_status"], "source_script_queued")
            self.assertEqual(rows[0]["notebooklm_status"], "not_started")

    def test_write_episode_artifacts_makes_section_inputs_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "episodes"
            sections = [
                make_section("9.2.3", "Global workspace theory"),
                make_section("9.2.4", "Multiple drafts model"),
            ]

            write_episode_artifacts(sections, output_dir)

            manifest = json.loads((output_dir / "group-001" / "manifest.json").read_text(encoding="utf-8"))
            readme = (output_dir / "group-001" / "README.md").read_text(encoding="utf-8")

            self.assertEqual(manifest["episode_id"], "group-001")
            self.assertEqual(manifest["section_ids"], ["9.2.3", "9.2.4"])
            self.assertEqual(
                manifest["research_inputs"],
                ["data/research/9.2.3.json", "data/research/9.2.4.json"],
            )
            self.assertEqual(manifest["sections"][0]["title"], "Global workspace theory")
            self.assertEqual(manifest["sections"][0]["research_path"], "data/research/9.2.3.json")
            self.assertEqual(
                manifest["sections"][0]["packet_path"],
                "packets/theories/9-2-3-global-workspace-theory.md",
            )
            self.assertEqual(manifest["script_job_manifest"], "jobs/source-scripts.jsonl")
            self.assertEqual(manifest["bundle_output_path"], "episodes/group-001/notebooklm_bundle/research_dossier.md")
            self.assertIn("This is one podcast episode group", readme)
            self.assertIn("section-level research records", readme)
            self.assertIn("factual NotebookLM source script", readme)
            self.assertIn("data/research/9.2.3.json", readme)


if __name__ == "__main__":
    unittest.main()
