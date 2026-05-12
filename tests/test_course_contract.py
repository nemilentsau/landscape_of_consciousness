import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.course_contract import DEFAULT_COURSE_CONTRACT, write_default_course_contract


class CourseContractTest(unittest.TestCase):
    def test_write_default_course_contract_records_static_production_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "course" / "course_contract.md"

            write_default_course_contract(path)

            text = path.read_text(encoding="utf-8")
            self.assertEqual(text, DEFAULT_COURSE_CONTRACT)
            self.assertIn("# Consciousness Course Contract", text)
            self.assertIn("## Course Purpose", text)
            self.assertIn("## Production Rules", text)
            self.assertIn("## Epistemic Discipline", text)
            self.assertIn("## NotebookLM Handoff Rules", text)
            self.assertIn("NotebookLM generates the conversational audio", text)
            self.assertNotIn("course memory", text.casefold())


if __name__ == "__main__":
    unittest.main()
