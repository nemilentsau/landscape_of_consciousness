import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.audio_reviews import episode_audio_status, write_audio_review


class AudioReviewsTest(unittest.TestCase):
    def test_write_audio_review_uses_production_status_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_path = root / "course" / "production-status.csv"
            status_path.parent.mkdir(parents=True)
            status_path.write_text(
                "group_id,section_id,packet_slug,research_status,script_status,notebooklm_status,notebook_url,"
                "audio_status,message\n"
                "group-006,26,26-reflections,researched,source_script_ready,notebooklm_bundle_ready,"
                "https://notebooklm.example/group-006,audio_ready,ready\n",
                encoding="utf-8",
            )

            path = write_audio_review(root, "group-006")

            self.assertEqual(path, root / "episodes" / "group-006" / "audio_review.md")
            review = path.read_text(encoding="utf-8")
            self.assertIn("Review status: pending_human_listen", review)
            self.assertIn("https://notebooklm.example/group-006", review)
            self.assertIn("Audio status from production ledger: audio_ready", review)

    def test_episode_audio_status_returns_latest_row_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_path = root / "course" / "production-status.csv"
            status_path.parent.mkdir(parents=True)
            status_path.write_text(
                "group_id,section_id,packet_slug,research_status,script_status,notebooklm_status,notebook_url,"
                "audio_status,message\n"
                "group-002,6,06-is-consciousness-primitive-fundamental,researched,source_script_ready,"
                "notebooklm_bundle_ready,https://example.test/first,audio_requested,requested\n"
                "group-002,7,07-identity-theory,researched,source_script_ready,notebooklm_bundle_ready,"
                "https://example.test/new,audio_ready,ready\n",
                encoding="utf-8",
            )

            status = episode_audio_status(root, "group-002")

            self.assertEqual(status["audio_status"], "audio_ready")
            self.assertEqual(status["notebook_url"], "https://example.test/new")

    def test_episode_audio_status_returns_empty_when_ledger_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            status = episode_audio_status(Path(tmp), "group-002")

            self.assertEqual(status, {})

    def test_write_audio_review_rejects_unknown_review_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Unsupported audio review status"):
                write_audio_review(Path(tmp), "group-006", review_status="approvedish")


if __name__ == "__main__":
    unittest.main()
