import unittest
from pathlib import Path

from consciousness_pipeline import __version__
from consciousness_pipeline.config import (
    AUDIO_FORMAT,
    AUDIO_LANGUAGE,
    AUDIO_LENGTH,
    DEFAULT_PDF,
    PROJECT_ROOT,
    STATUS_VALUES,
)


class ConfigTest(unittest.TestCase):
    def test_project_paths_and_audio_defaults(self):
        active_checkout_root = Path(__file__).resolve().parents[1]

        self.assertEqual(__version__, "0.1.0")
        self.assertEqual(PROJECT_ROOT, active_checkout_root)
        self.assertEqual(
            DEFAULT_PDF,
            PROJECT_ROOT
            / "papers"
            / "A-landscape-of-consciousness--Toward-a-taxonom_2024_Progress-in-Biophysics-a.pdf",
        )
        self.assertEqual(AUDIO_FORMAT, "Deep Dive")
        self.assertEqual(AUDIO_LENGTH, "Long")
        self.assertEqual(AUDIO_LANGUAGE, "English")
        self.assertIn("manual_action_required", STATUS_VALUES)
        self.assertIsInstance(PROJECT_ROOT, Path)


if __name__ == "__main__":
    unittest.main()
