import os
import tomllib
import unittest

from consciousness_pipeline.config import PROJECT_ROOT


class ToolingConfigTest(unittest.TestCase):
    def test_project_uses_uv_with_repo_venv_and_quality_tools(self):
        pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        dev_dependencies = set(pyproject["project"]["optional-dependencies"]["dev"])
        pyright = pyproject["tool"]["pyright"]
        package_include = pyproject["tool"]["setuptools"]["packages"]["find"]["include"]

        self.assertIn("pypdf", pyproject["project"]["dependencies"])
        self.assertIn("ruff", dev_dependencies)
        self.assertIn("pyright", dev_dependencies)
        self.assertEqual(package_include, ["consciousness_pipeline*"])
        self.assertEqual(pyright["venvPath"], ".")
        self.assertEqual(pyright["venv"], ".venv")
        self.assertIn(".venv/", (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8"))

    def test_claude_instructions_are_symlinked_to_agents(self):
        agents = PROJECT_ROOT / "AGENTS.md"
        claude = PROJECT_ROOT / "CLAUDE.md"

        self.assertTrue(agents.exists())
        self.assertTrue(claude.is_symlink())
        self.assertEqual(os.readlink(claude), "AGENTS.md")

        instructions = agents.read_text(encoding="utf-8")
        self.assertIn("Use `uv` for Python", instructions)
        self.assertIn("dedicated `.venv`", instructions)
        self.assertIn("uv run ruff check .", instructions)
        self.assertIn("uv run pyright", instructions)

    def test_episode_runner_script_uses_uv_cli_command(self):
        script = PROJECT_ROOT / "scripts" / "run_episode"

        self.assertTrue(script.exists())
        self.assertTrue(os.access(script, os.X_OK))
        text = script.read_text(encoding="utf-8")
        self.assertIn("uv run python -m consciousness_pipeline.cli run-episode", text)


if __name__ == "__main__":
    unittest.main()
