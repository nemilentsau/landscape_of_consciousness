import subprocess
import sys
import unittest


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
        self.assertIn("all", result.stdout)


if __name__ == "__main__":
    unittest.main()
