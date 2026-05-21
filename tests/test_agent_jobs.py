import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from consciousness_pipeline.agent_jobs import build_job_prompt, write_agent_job_artifacts
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
            script_jobs = read_jsonl(root / "jobs" / "source-scripts.jsonl")
            capsule_jobs = read_jsonl(root / "jobs" / "episode-capsules.jsonl")
            selection_jobs = read_jsonl(root / "jobs" / "course-context-selections.jsonl")
            review_jobs = read_jsonl(root / "jobs" / "episode-reviews.jsonl")
            serialized = json.dumps(
                {
                    "research": research_jobs,
                    "scripts": script_jobs,
                    "capsules": capsule_jobs,
                    "selections": selection_jobs,
                    "reviews": review_jobs,
                }
            ).lower()

            self.assertEqual(len(research_jobs), 2)
            self.assertEqual(research_jobs[0]["kind"], "research")
            self.assertEqual(research_jobs[0]["job_id"], "research-9.2.3")
            self.assertEqual(research_jobs[0]["output_path"], "data/research/9.2.3.json")
            self.assertEqual(research_jobs[0]["schema_path"], "schemas/research-record.schema.json")
            self.assertEqual(research_jobs[0]["agents"], ["codex_exec", "claude_headless"])

            self.assertEqual(len(script_jobs), 1)
            self.assertEqual(script_jobs[0]["kind"], "source_script")
            self.assertEqual(script_jobs[0]["prompt_contract"], "notebooklm_factual_source_script_v2")
            self.assertEqual(script_jobs[0]["duration_target"], "long_form")
            self.assertEqual(script_jobs[0]["section_ids"], ["9.2.3", "9.2.4"])
            self.assertEqual(script_jobs[0]["episode_manifest_path"], "episodes/group-001/manifest.json")
            self.assertIn("episodes/group-001/manifest.json", script_jobs[0]["input_paths"])
            self.assertIn("episodes/group-001/course_context.md", script_jobs[0]["input_paths"])
            self.assertEqual(script_jobs[0]["output_path"], "episodes/group-001/script.json")
            self.assertEqual(
                script_jobs[0]["bundle_output_path"],
                "episodes/group-001/notebooklm_bundle/research_dossier.md",
            )
            self.assertIn("computer_use", script_jobs[0]["notebooklm_handoff"])

            self.assertEqual(len(capsule_jobs), 1)
            self.assertEqual(capsule_jobs[0]["kind"], "course_episode_capsule")
            self.assertEqual(capsule_jobs[0]["job_id"], "group-001-capsule")
            self.assertEqual(capsule_jobs[0]["group_id"], "group-001")
            self.assertEqual(capsule_jobs[0]["episode_manifest_path"], "episodes/group-001/manifest.json")
            self.assertEqual(
                capsule_jobs[0]["accepted_dossier_path"],
                "episodes/group-001/notebooklm_bundle/research_dossier.md",
            )
            self.assertIn("course/course_contract.md", capsule_jobs[0]["input_paths"])
            self.assertEqual(capsule_jobs[0]["output_path"], "course/episode_capsules/group-001.json")
            self.assertEqual(capsule_jobs[0]["schema_path"], "schemas/episode-capsule.schema.json")

            self.assertEqual(len(selection_jobs), 1)
            self.assertEqual(selection_jobs[0]["kind"], "course_context_selection")
            self.assertEqual(selection_jobs[0]["job_id"], "group-001-context-selection")
            self.assertEqual(selection_jobs[0]["group_id"], "group-001")
            self.assertEqual(selection_jobs[0]["episode_manifest_path"], "episodes/group-001/manifest.json")
            self.assertIn("course/callback_index.json", selection_jobs[0]["input_paths"])
            self.assertEqual(selection_jobs[0]["output_path"], "episodes/group-001/context_selection.json")
            self.assertEqual(selection_jobs[0]["schema_path"], "schemas/course-context-selection.schema.json")

            self.assertEqual(len(review_jobs), 1)
            self.assertEqual(review_jobs[0]["kind"], "episode_review")
            self.assertEqual(review_jobs[0]["job_id"], "group-001-review")
            self.assertEqual(review_jobs[0]["group_id"], "group-001")
            self.assertEqual(review_jobs[0]["episode_manifest_path"], "episodes/group-001/manifest.json")
            self.assertEqual(
                review_jobs[0]["source_script_path"],
                "episodes/group-001/script.json",
            )
            self.assertEqual(
                review_jobs[0]["dossier_path"],
                "episodes/group-001/notebooklm_bundle/research_dossier.md",
            )
            self.assertEqual(review_jobs[0]["output_path"], "episodes/group-001/review.json")
            self.assertEqual(review_jobs[0]["schema_path"], "schemas/episode-review.schema.json")

            self.assertTrue((root / "schemas" / "research-record.schema.json").exists())
            self.assertTrue((root / "schemas" / "episode-capsule.schema.json").exists())
            self.assertTrue((root / "schemas" / "course-context-selection.schema.json").exists())
            self.assertTrue((root / "schemas" / "episode-review.schema.json").exists())
            source_script_schema = json.loads((root / "schemas" / "source-script.schema.json").read_text())
            self.assertIn("research_dossier_markdown", source_script_schema["required"])
            self.assertNotIn("script_markdown", source_script_schema["properties"])
            self.assertNotIn("playwright", serialized)

            sections_path = root / "data" / "extracted" / "sections.json"
            sections_path.parent.mkdir(parents=True)
            sections_path.write_text(
                json.dumps([section.to_dict() for section in sections], ensure_ascii=False),
                encoding="utf-8",
            )
            prompt = build_job_prompt(script_jobs[0], root)
            self.assertIn("factual NotebookLM source dossier", prompt)
            self.assertIn("Do not write dialogue", prompt)
            self.assertIn("NotebookLM will generate the conversational audio", prompt)
            self.assertIn("Do not import or rely on", prompt)
            self.assertIn("`jsonschema`", prompt)
            self.assertIn("--stage dossier", prompt)
            self.assertNotIn("opening dispute", prompt)
            self.assertNotIn("cross-examination", prompt)

            (root / "course").mkdir(parents=True, exist_ok=True)
            (root / "course" / "course_contract.md").write_text("Static course rules.", encoding="utf-8")
            dossier_path = root / "episodes" / "group-001" / "notebooklm_bundle" / "research_dossier.md"
            dossier_path.parent.mkdir(parents=True, exist_ok=True)
            dossier_path.write_text("Accepted factual source dossier.", encoding="utf-8")
            capsule_prompt = build_job_prompt(capsule_jobs[0], root)
            self.assertIn("extract durable course continuity", capsule_prompt)
            self.assertIn("do not rewrite the whole course", capsule_prompt)
            self.assertIn("do not add new facts", capsule_prompt)
            self.assertIn("Default memory budget", capsule_prompt)
            self.assertIn("Callback family is required but provisional and free-form", capsule_prompt)
            self.assertIn("Accepted factual source dossier.", capsule_prompt)

            (root / "course" / "callback_index.json").write_text("{}", encoding="utf-8")
            selection_prompt = build_job_prompt(selection_jobs[0], root)
            self.assertIn("Select course continuity context", selection_prompt)
            self.assertIn("compact capsule metadata", selection_prompt)
            self.assertIn("Return only JSON matching the schema", selection_prompt)
            self.assertIn("import or rely on", selection_prompt)
            self.assertIn("`jsonschema`", selection_prompt)

            source_script_path = root / "episodes" / "group-001" / "script.json"
            source_script_path.write_text(
                json.dumps(
                    {
                        "episode_id": "group-001",
                        "title": "Materialism theories Part 1",
                        "episode_question": "What is the strongest case for this cluster?",
                        "duration_target": "long_form",
                        "research_dossier_markdown": "Accepted factual source dossier.",
                        "citations": ["Kuhn 2024"],
                        "missing_inputs": [],
                    }
                ),
                encoding="utf-8",
            )
            review_prompt = build_job_prompt(review_jobs[0], root)
            self.assertIn("review gate", review_prompt)
            self.assertIn("Approve only if", review_prompt)
            self.assertIn("Do not repair the dossier", review_prompt)
            self.assertIn("Accepted factual source dossier.", review_prompt)

    def test_build_job_prompt_removes_nul_bytes_from_extracted_pdf_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            section = make_section("8", "A landscape")
            section = Section(
                section_id=section.section_id,
                title=section.title,
                level=section.level,
                start_page=8,
                end_page=11,
                taxonomy_path=section.taxonomy_path,
                text="Figure reference contains a PDF extraction artifact: \x00 8.",
                slug=section.slug,
            )
            sections_path = root / "data" / "extracted" / "sections.json"
            sections_path.parent.mkdir(parents=True)
            sections_path.write_text(json.dumps([section.to_dict()], ensure_ascii=False), encoding="utf-8")
            job = {
                "kind": "research",
                "job_id": "research-8",
                "section_id": "8",
                "output_path": "data/research/8.json",
                "schema_path": "schemas/research-record.schema.json",
            }

            prompt = build_job_prompt(job, root)

            self.assertNotIn("\x00", prompt)
            self.assertIn("artifact:  8.", prompt)

    def test_build_script_prompt_includes_existing_episode_course_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            section = make_section("6", "Is consciousness primitive/fundamental?", "Top-level sections")
            sections_path = root / "data" / "extracted" / "sections.json"
            sections_path.parent.mkdir(parents=True)
            sections_path.write_text(json.dumps([section.to_dict()], ensure_ascii=False), encoding="utf-8")
            context_path = root / "episodes" / "group-002" / "course_context.md"
            context_path.parent.mkdir(parents=True)
            context_path.write_text(
                "Group 001 already covered the hard problem. Do not restart from scratch.",
                encoding="utf-8",
            )
            job = {
                "kind": "source_script",
                "job_id": "group-002-script",
                "group_id": "group-002",
                "title": "Top-level sections Part 2",
                "episode_question": "What is the strongest case for this cluster, and where does it break?",
                "section_ids": ["6"],
                "episode_manifest_path": "episodes/group-002/manifest.json",
                "output_path": "episodes/group-002/script.json",
                "schema_path": "schemas/source-script.schema.json",
                "notebooklm_handoff": "computer_use_after_script_bundle",
                "notebooklm_bundle_dir": "episodes/group-002/notebooklm_bundle",
                "bundle_output_path": "episodes/group-002/notebooklm_bundle/research_dossier.md",
            }

            prompt = build_job_prompt(job, root)

            self.assertIn("Course context path: episodes/group-002/course_context.md", prompt)
            self.assertIn("Group 001 already covered the hard problem", prompt)
            self.assertIn("Use this context to continue the course", prompt)
            self.assertIn("## Course Continuity Grounding", prompt)
            self.assertIn("Do not bury course continuity inside the episode-scope section.", prompt)


if __name__ == "__main__":
    unittest.main()
