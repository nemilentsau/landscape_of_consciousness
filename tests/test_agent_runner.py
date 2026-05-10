import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from consciousness_pipeline.agent_runner import build_claude_command, build_codex_command, check_agent_available


class AgentRunnerCommandTest(unittest.TestCase):
    def test_build_codex_command_uses_exec_schema_and_output_file(self):
        job = {
            "output_path": "data/research/9.2.3.json",
            "schema_path": "schemas/research-record.schema.json",
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

    def test_build_claude_command_uses_bare_print_mode_and_json_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            schema_path = root / "schemas" / "source-script.schema.json"
            schema_path.parent.mkdir(parents=True)
            schema = {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            job = {"schema_path": "schemas/source-script.schema.json"}
            prompt = "Write a factual NotebookLM source dossier."

            command = build_claude_command(job, prompt, root)

            self.assertEqual(command[:3], ["claude", "--bare", "-p"])
            self.assertIn(prompt, command)
            self.assertIn("--output-format", command)
            self.assertIn("json", command)
            self.assertIn("--json-schema", command)
            self.assertIn(json.dumps(schema), command)

    @patch("consciousness_pipeline.agent_runner.subprocess.run")
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
