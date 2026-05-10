import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.research import write_research_readme


class ResearchArtifactsTest(unittest.TestCase):
    def test_write_research_readme_explains_section_episode_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = Path(tmp) / "data" / "research"

            write_research_readme(research_dir)

            readme = (research_dir / "README.md").read_text(encoding="utf-8")
            self.assertIn("section-level", readme)
            self.assertIn("not podcast episodes", readme)
            self.assertIn("episodes/<group-id>/manifest.json", readme)
            self.assertIn("course/episode-map.json", readme)


if __name__ == "__main__":
    unittest.main()
