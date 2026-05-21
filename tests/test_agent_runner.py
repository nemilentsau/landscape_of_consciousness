import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from consciousness_pipeline.agents.runner import (
    build_claude_command,
    build_codex_command,
    check_agent_available,
    run_job,
)
from consciousness_pipeline.contracts.schemas import SOURCE_SCRIPT_SCHEMA


class AgentRunnerCommandTest(unittest.TestCase):
    def test_build_codex_command_uses_exec_schema_and_output_file(self):
        job = {
            "kind": "research",
            "output_path": "data/research/9.2.3.json",
        }
        prompt = "Research the consciousness theory and return JSON."

        command = build_codex_command(job, prompt)

        self.assertEqual(command[:2], ["codex", "exec"])
        self.assertIn("--sandbox", command)
        self.assertIn("workspace-write", command)
        self.assertIn("--output-schema", command)
        self.assertIn("schemas/research-record.schema.json", command)
        self.assertIn("-o", command)
        self.assertIn("data/research/9.2.3.json", command)
        self.assertEqual(command[-1], prompt)

    def test_build_claude_command_uses_print_mode_local_auth_and_json_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            job = {"kind": "source_script"}
            prompt = "Write a factual NotebookLM source dossier."

            command = build_claude_command(job, prompt, root)

            self.assertEqual(command[:2], ["claude", "-p"])
            self.assertIn(prompt, command)
            self.assertNotIn("--bare", command)
            self.assertNotIn("--allowedTools", command)
            self.assertIn("--output-format", command)
            self.assertIn("json", command)
            self.assertIn("--json-schema", command)
            self.assertIn(json.dumps(SOURCE_SCRIPT_SCHEMA, ensure_ascii=False), command)

    @patch("consciousness_pipeline.agents.runner.subprocess.run")
    def test_run_claude_job_allows_comparison_output_paths_and_writes_dossier_bundle(self, run):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sections_path = root / "data" / "extracted" / "sections.json"
            sections_path.parent.mkdir(parents=True)
            sections_path.write_text(
                json.dumps(
                    [
                        {
                            "section_id": "6",
                            "title": "Is consciousness primitive/fundamental?",
                            "level": 1,
                            "start_page": 6,
                            "end_page": 6,
                            "taxonomy_path": ["Is consciousness primitive/fundamental?"],
                            "text": "Kuhn section text.",
                            "slug": "06-is-consciousness-primitive-fundamental",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            manifest_path = root / "jobs" / "source-scripts.jsonl"
            manifest_path.parent.mkdir(parents=True)
            job = {
                "job_id": "group-002-script",
                "kind": "source_script",
                "group_id": "group-002",
                "title": "Top-level sections Part 2",
                "episode_question": "What is the strongest case for this cluster, and where does it break?",
                "section_ids": ["6"],
                "episode_manifest_path": "episodes/group-002/manifest.json",
                "output_path": "episodes/group-002/script.json",
                "notebooklm_handoff": "computer_use_after_script_bundle",
                "notebooklm_bundle_dir": "episodes/group-002/notebooklm_bundle",
                "bundle_output_path": "episodes/group-002/notebooklm_bundle/research_dossier.md",
            }
            manifest_path.write_text(json.dumps(job) + "\n", encoding="utf-8")
            structured_output = {
                "episode_id": "group-002",
                "title": "Top-level sections Part 2",
                "episode_question": job["episode_question"],
                "duration_target": "long_form",
                "research_dossier_markdown": "# Claude dossier\n\nFactual material.",
                "citations": ["Kuhn 2024"],
                "missing_inputs": [],
            }
            run.side_effect = [
                subprocess.CompletedProcess(args=["claude", "--version"], returncode=0, stdout="2.1.138", stderr=""),
                subprocess.CompletedProcess(
                    args=["claude", "-p"],
                    returncode=0,
                    stdout=json.dumps({"result": structured_output}),
                    stderr="",
                ),
            ]

            run_job(
                manifest_path,
                "group-002-script",
                "claude",
                root=root,
                output_path=Path("episodes/group-002/claude/script.json"),
                bundle_output_path=Path("episodes/group-002/claude/notebooklm_bundle/research_dossier.md"),
            )

            script_path = root / "episodes" / "group-002" / "claude" / "script.json"
            bundle_path = root / "episodes" / "group-002" / "claude" / "notebooklm_bundle" / "research_dossier.md"
            self.assertEqual(json.loads(script_path.read_text(encoding="utf-8")), structured_output)
            self.assertEqual(bundle_path.read_text(encoding="utf-8"), structured_output["research_dossier_markdown"])

    @patch("consciousness_pipeline.agents.runner.subprocess.run")
    def test_run_claude_capsule_job_writes_structured_output_without_dossier_bundle(self, run):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "course").mkdir(parents=True)
            (root / "course" / "course_contract.md").write_text("Static course rules.", encoding="utf-8")
            episode_dir = root / "episodes" / "group-002"
            episode_dir.mkdir(parents=True)
            (episode_dir / "manifest.json").write_text('{"episode_id": "group-002"}', encoding="utf-8")
            dossier = episode_dir / "notebooklm_bundle" / "research_dossier.md"
            dossier.parent.mkdir(parents=True)
            dossier.write_text("# Accepted dossier\n", encoding="utf-8")
            manifest_path = root / "jobs" / "episode-capsules.jsonl"
            manifest_path.parent.mkdir(parents=True)
            job = {
                "job_id": "group-002-capsule",
                "kind": "course_episode_capsule",
                "group_id": "group-002",
                "title": "Top-level sections Part 2",
                "episode_manifest_path": "episodes/group-002/manifest.json",
                "accepted_dossier_path": "episodes/group-002/notebooklm_bundle/research_dossier.md",
                "output_path": "course/episode_capsules/group-002.json",
            }
            manifest_path.write_text(json.dumps(job) + "\n", encoding="utf-8")
            structured_output = {"episode_id": "group-002"}
            run.side_effect = [
                subprocess.CompletedProcess(args=["claude", "--version"], returncode=0, stdout="2.1.138", stderr=""),
                subprocess.CompletedProcess(
                    args=["claude", "-p"],
                    returncode=0,
                    stdout=json.dumps({"result": structured_output}),
                    stderr="",
                ),
            ]

            run_job(manifest_path, "group-002-capsule", "claude", root=root)

            output_path = root / "course" / "episode_capsules" / "group-002.json"
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8")), structured_output)
            self.assertFalse((root / "episodes" / "group-002" / "notebooklm_bundle" / "script.md").exists())

    @patch("consciousness_pipeline.agents.runner.subprocess.run")
    def test_check_agent_available_reports_broken_cli_stderr(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=["codex", "--version"],
            returncode=1,
            stdout="",
            stderr="spawn missing vendored binary ENOENT",
        )

        with self.assertRaises(RuntimeError) as context:
            check_agent_available("codex")

        self.assertIn("codex CLI is not usable", str(context.exception))
        self.assertIn("ENOENT", str(context.exception))


if __name__ == "__main__":
    unittest.main()
