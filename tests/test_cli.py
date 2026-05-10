import subprocess
import sys
import unittest
from unittest.mock import patch

from consciousness_pipeline import cli


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


if __name__ == "__main__":
    unittest.main()
