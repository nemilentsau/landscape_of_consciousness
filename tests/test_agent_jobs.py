import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from consciousness_pipeline.agent_jobs import write_agent_job_artifacts
from consciousness_pipeline.models import Section


def make_section(section_id: str, title: str, parent: str = "Materialism theories") -> Section:
    return Section(
        section_id=section_id,
        title=title,
        level=3,
        start_page=20,
        end_page=21,
        taxonomy_path=[parent, "Neurobiological theories", title],
        text=f"{title} section text.",
        slug=section_id.replace(".", "-") + "-" + title.lower().replace(" ", "-"),
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class AgentJobGenerationTest(unittest.TestCase):
    def test_write_agent_job_artifacts_generates_headless_manifests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sections = [
                make_section("9.2.3", "Global workspace theory"),
                make_section("9.2.4", "Multiple drafts model"),
            ]

            write_agent_job_artifacts(
                sections,
                jobs_dir=root / "jobs",
                schemas_dir=root / "schemas",
                episodes_dir=root / "episodes",
            )

            research_jobs = read_jsonl(root / "jobs" / "research.jsonl")
            script_jobs = read_jsonl(root / "jobs" / "podcast-scripts.jsonl")
            serialized = json.dumps({"research": research_jobs, "scripts": script_jobs}).lower()

            self.assertEqual(len(research_jobs), 2)
            self.assertEqual(research_jobs[0]["kind"], "research")
            self.assertEqual(research_jobs[0]["job_id"], "research-9.2.3")
            self.assertEqual(research_jobs[0]["output_path"], "data/research/9.2.3.json")
            self.assertEqual(research_jobs[0]["schema_path"], "schemas/research-record.schema.json")
            self.assertEqual(research_jobs[0]["agents"], ["codex_exec", "claude_headless"])

            self.assertEqual(len(script_jobs), 1)
            self.assertEqual(script_jobs[0]["kind"], "podcast_script")
            self.assertEqual(script_jobs[0]["duration_target"], "long_form")
            self.assertEqual(script_jobs[0]["section_ids"], ["9.2.3", "9.2.4"])
            self.assertEqual(script_jobs[0]["output_path"], "episodes/group-001/script.json")
            self.assertIn("computer_use", script_jobs[0]["notebooklm_handoff"])

            self.assertTrue((root / "schemas" / "research-record.schema.json").exists())
            self.assertTrue((root / "schemas" / "podcast-script.schema.json").exists())
            self.assertNotIn("playwright", serialized)


if __name__ == "__main__":
    unittest.main()
