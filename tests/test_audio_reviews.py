import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.episodes.audio_reviews import (
    NotebookLMStatusError,
    episode_audio_status,
    record_notebooklm_status,
    write_audio_review,
)


def write_status(path: Path) -> None:
    path.parent.mkdir(parents=True)
    path.write_text(
        "group_id,section_id,packet_slug,research_status,script_status,notebooklm_status,notebook_url,"
        "audio_status,message\n"
        "group-001,1,one,researched,source_script_ready,notebooklm_bundle_ready,,not_started,\n"
        "group-001,2,two,researched,source_script_ready,notebooklm_bundle_ready,,not_started,\n"
        "group-002,3,three,researched,source_script_ready,notebooklm_bundle_ready,,not_started,\n",
        encoding="utf-8",
    )


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

    def test_record_notebooklm_status_updates_all_episode_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_path = root / "course" / "production-status.csv"
            write_status(status_path)

            path = record_notebooklm_status(
                root,
                "group-001",
                "audio_requested",
                notebook_url="https://notebooklm.example/group-001",
                message="NotebookLM accepted Long Deep Dive audio request from six-file bundle",
            )

            self.assertEqual(path, status_path)
            rows = status_path.read_text(encoding="utf-8").splitlines()
            self.assertIn(
                "group-001,1,one,researched,source_script_ready,notebooklm_bundle_ready,"
                "https://notebooklm.example/group-001,audio_requested,"
                "NotebookLM accepted Long Deep Dive audio request from six-file bundle",
                rows,
            )
            self.assertIn(
                "group-001,2,two,researched,source_script_ready,notebooklm_bundle_ready,"
                "https://notebooklm.example/group-001,audio_requested,"
                "NotebookLM accepted Long Deep Dive audio request from six-file bundle",
                rows,
            )
            self.assertIn(
                "group-002,3,three,researched,source_script_ready,notebooklm_bundle_ready,,not_started,",
                rows,
            )

    def test_record_notebooklm_status_allows_retrospective_request_without_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_path = root / "course" / "production-status.csv"
            write_status(status_path)

            record_notebooklm_status(
                root,
                "group-001",
                "audio_requested",
                message="Retrospective reconciliation: handoff started before URL capture was enforced",
            )

            status = episode_audio_status(root, "group-001")
            self.assertEqual(status["audio_status"], "audio_requested")
            self.assertNotIn("notebook_url", status)

    def test_record_notebooklm_status_requires_url_for_ready_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_status(root / "course" / "production-status.csv")

            with self.assertRaisesRegex(NotebookLMStatusError, "requires a NotebookLM URL"):
                record_notebooklm_status(root, "group-001", "audio_ready", message="Audio is available")

    def test_record_notebooklm_status_requires_message_for_verified_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_status(root / "course" / "production-status.csv")

            with self.assertRaisesRegex(NotebookLMStatusError, "requires a message"):
                record_notebooklm_status(root, "group-001", "audio_requested")

    def test_record_notebooklm_status_rejects_unknown_audio_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_status(root / "course" / "production-status.csv")

            with self.assertRaisesRegex(NotebookLMStatusError, "Unsupported audio status"):
                record_notebooklm_status(root, "group-001", "maybe_ready", message="unclear")

    def test_record_notebooklm_status_rejects_missing_episode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_status(root / "course" / "production-status.csv")

            with self.assertRaisesRegex(NotebookLMStatusError, "group-999"):
                record_notebooklm_status(root, "group-999", "audio_requested", message="No matching rows")

    def test_record_notebooklm_status_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_path = root / "course" / "production-status.csv"
            write_status(status_path)

            record_notebooklm_status(
                root,
                "group-001",
                "audio_requested",
                notebook_url="https://notebooklm.example/group-001",
                message="NotebookLM accepted request",
            )
            first_write = status_path.read_text(encoding="utf-8")
            record_notebooklm_status(
                root,
                "group-001",
                "audio_requested",
                notebook_url="https://notebooklm.example/group-001",
                message="NotebookLM accepted request",
            )

            self.assertEqual(status_path.read_text(encoding="utf-8"), first_write)


if __name__ == "__main__":
    unittest.main()
