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


if __name__ == "__main__":
    unittest.main()
