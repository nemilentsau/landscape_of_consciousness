import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from consciousness_pipeline import cli
from consciousness_pipeline.models import ResearchRecord, Section, SourceRecord


def make_section() -> Section:
    return Section(
        section_id="9.2.3",
        title="Global workspace theory",
        level=3,
        start_page=10,
        end_page=12,
        taxonomy_path=("Materialism", "Neurobiological theories", "Global workspace theory"),
        text="Section text",
        slug="09-02-03-global-workspace-theory",
    )


def make_research() -> ResearchRecord:
    return ResearchRecord(
        section_id="9.2.3",
        opening_question="What does global broadcast explain?",
        core_claim="Conscious access depends on global availability.",
        strongest_case="It explains report and flexible control.",
        best_objections="It may not explain phenomenal character.",
        credibility="Mainstream scientific theory with active debate.",
        listener_hooks=(),
        sources=(
            SourceRecord(
                kind="primary",
                title="A Cognitive Theory of Consciousness",
                url="https://example.test/baars",
                citation="Baars, B. J. (1988).",
            ),
        ),
    )


class CliTest(unittest.TestCase):
    def test_help_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "consciousness_pipeline.cli", "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("extract", result.stdout)
        self.assertIn("jobs", result.stdout)
        self.assertIn("run-job", result.stdout)
        self.assertIn("run-episode", result.stdout)
        self.assertIn("accept-episode", result.stdout)
        self.assertIn("select-context", result.stdout)
        self.assertIn("write-contract", result.stdout)
        self.assertIn("bundle-sources", result.stdout)
        self.assertIn("all", result.stdout)

    def test_runtime_errors_exit_without_traceback(self):
        argv = [
            "cli.py",
            "run-job",
            "--manifest",
            "jobs/research.jsonl",
            "--job-id",
            "research-9.2.3",
            "--agent",
            "codex",
        ]

        with patch.object(sys, "argv", argv), patch(
            "consciousness_pipeline.cli.run_job",
            side_effect=RuntimeError("codex CLI is not usable: ENOENT"),
        ):
            with self.assertRaises(SystemExit) as context:
                cli.main()

        self.assertIn("codex CLI is not usable", str(context.exception))

    def test_bundle_sources_command_writes_episode_source_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            section = make_section()
            extracted_dir = root / "data" / "extracted"
            research_dir = root / "data" / "research"
            episodes_dir = root / "episodes"
            extracted_dir.mkdir(parents=True)
            research_dir.mkdir(parents=True)
            (episodes_dir / "group-001").mkdir(parents=True)
            (extracted_dir / "sections.json").write_text(json.dumps([section.to_dict()]), encoding="utf-8")
            (research_dir / "9.2.3.json").write_text(json.dumps(make_research().to_dict()), encoding="utf-8")
            (episodes_dir / "group-001" / "manifest.json").write_text(
                json.dumps(
                    {
                        "episode_id": "group-001",
                        "section_ids": ["9.2.3"],
                        "notebooklm_bundle_dir": "episodes/group-001/notebooklm_bundle",
                    }
                ),
                encoding="utf-8",
            )
            argv = ["cli.py", "bundle-sources", "--episode-id", "group-001"]

            with patch.object(sys, "argv", argv), patch.object(cli, "PROJECT_ROOT", root), patch.object(
                cli, "EXTRACTED_DIR", extracted_dir
            ), patch.object(cli, "RESEARCH_DIR", research_dir), patch.object(cli, "EPISODES_DIR", episodes_dir):
                cli.main()

            source_path = (
                episodes_dir
                / "group-001"
                / "notebooklm_bundle"
                / "sources"
                / "09-02-03-global-workspace-theory.md"
            )
            self.assertTrue(source_path.exists())
            self.assertIn("## Core Claim", source_path.read_text(encoding="utf-8"))

    def test_write_context_command_writes_episode_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            course_dir = root / "course"
            episodes_dir = root / "episodes"
            group_dir = episodes_dir / "group-003"
            group_dir.mkdir(parents=True)
            (group_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "episode_id": "group-003",
                        "title": "Top-level sections Part 3",
                        "episode_question": "What is the strongest case for this cluster, and where does it break?",
                        "sections": [
                            {"section_id": "11", "title": "Quantum theories", "pages": "13-16"},
                            {"section_id": "12", "title": "Integrated information theory", "pages": "16-20"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            argv = ["cli.py", "write-context", "--episode-id", "group-003"]

            with patch.object(sys, "argv", argv), patch.object(cli, "COURSE_DIR", course_dir), patch.object(
                cli, "EPISODES_DIR", episodes_dir
            ):
                cli.main()

            context_path = group_dir / "course_context.md"
            self.assertTrue(context_path.exists())
            context = context_path.read_text(encoding="utf-8")
            self.assertTrue((course_dir / "course_contract.md").exists())
            self.assertIn("Quantum theories", context)
            self.assertIn("Integrated information theory", context)
            self.assertIn("## Source Priority", context)

    def test_run_episode_command_delegates_to_ordered_runner(self):
        argv = ["cli.py", "run-episode", "--episode-id", "group-003", "--agent", "codex"]

        with patch.object(sys, "argv", argv), patch("consciousness_pipeline.cli.run_episode") as run_episode:
            cli.main()

        run_episode.assert_called_once_with(
            "group-003",
            "codex",
            dry_run=False,
            auto_accept=False,
            review_agent=None,
        )

    def test_run_episode_command_accepts_review_agent_for_auto_accept(self):
        argv = [
            "cli.py",
            "run-episode",
            "--episode-id",
            "group-003",
            "--agent",
            "codex",
            "--auto-accept",
            "--review-agent",
            "claude",
        ]

        with patch.object(sys, "argv", argv), patch("consciousness_pipeline.cli.run_episode") as run_episode:
            cli.main()

        run_episode.assert_called_once_with(
            "group-003",
            "codex",
            dry_run=False,
            auto_accept=True,
            review_agent="claude",
        )

    def test_run_episode_auto_accept_defaults_to_claude_reviewer(self):
        argv = [
            "cli.py",
            "run-episode",
            "--episode-id",
            "group-003",
            "--agent",
            "codex",
            "--auto-accept",
        ]

        with patch.object(sys, "argv", argv), patch("consciousness_pipeline.cli.run_episode") as run_episode:
            cli.main()

        run_episode.assert_called_once_with(
            "group-003",
            "codex",
            dry_run=False,
            auto_accept=True,
            review_agent="claude",
        )

    def test_select_context_command_runs_selector_and_writes_context(self):
        argv = ["cli.py", "select-context", "--episode-id", "group-005", "--agent", "claude"]

        with patch.object(sys, "argv", argv), patch(
            "consciousness_pipeline.cli.select_episode_context"
        ) as select_episode_context:
            cli.main()

        select_episode_context.assert_called_once_with("group-005", "claude", dry_run=False)

    def test_accept_episode_command_delegates_to_acceptance_checkpoint(self):
        argv = ["cli.py", "accept-episode", "--episode-id", "group-002", "--agent", "claude"]

        with patch.object(sys, "argv", argv), patch("consciousness_pipeline.cli.accept_episode") as accept_episode:
            cli.main()

        accept_episode.assert_called_once_with("group-002", "claude", dry_run=False)

    def test_write_contract_command_writes_static_course_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            course_dir = Path(tmp) / "course"
            argv = ["cli.py", "write-contract"]

            with patch.object(sys, "argv", argv), patch.object(cli, "COURSE_DIR", course_dir):
                cli.main()

            contract_path = course_dir / "course_contract.md"
            self.assertTrue(contract_path.exists())
            self.assertIn("## NotebookLM Handoff Rules", contract_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
