import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from consciousness_pipeline.episodes.acceptance import EpisodeAcceptanceError, accept_episode


def write_status(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "group_id",
                "section_id",
                "packet_slug",
                "research_status",
                "script_status",
                "notebooklm_status",
                "notebook_url",
                "audio_status",
                "message",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(
            {
                "group_id": "group-002",
                "section_id": "6",
                "packet_slug": "06-is-consciousness-primitive-fundamental",
                "research_status": "researched",
                "script_status": "source_script_queued",
                "notebooklm_status": "not_started",
                "notebook_url": "",
                "audio_status": "not_started",
                "message": "",
            }
        )


def make_capsule(root: Path) -> dict[str, object]:
    return {
        "schema_version": "episode_capsule_v1",
        "episode_id": "group-002",
        "title": "Top-level sections Part 2",
        "accepted_dossier_path": "episodes/group-002/notebooklm_bundle/research_dossier.md",
        "section_ids": ["6"],
        "thesis": "The episode established the physicalist fork without treating it as settled.",
        "durable_concepts": [
            {
                "concept": "brain_dependence_vs_reduction",
                "summary": "Brain dependence does not settle identity or explanation.",
                "source_path": "episodes/group-002/notebooklm_bundle/research_dossier.md",
            }
        ],
        "recurring_distinctions": ["correlation vs explanation"],
        "do_not_reexplain": ["Do not restart the hard problem setup."],
        "open_tensions": ["Physical dependence and phenomenal explanation remain separable."],
        "callbacks": [
            {
                "concept": "hard_problem",
                "family": "target_phenomenon_discipline",
                "tags": ["hard_problem", "phenomenal_consciousness"],
                "summary": "Use as the central pressure point.",
                "source_path": "episodes/group-002/notebooklm_bundle/research_dossier.md",
                "useful_for_future_sections": ["integrated information theory"],
            }
        ],
    }


class EpisodeAcceptanceTest(unittest.TestCase):
    def test_accept_episode_runs_capsule_job_validates_output_and_updates_index_and_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dossier = root / "episodes" / "group-002" / "notebooklm_bundle" / "research_dossier.md"
            dossier.parent.mkdir(parents=True)
            dossier.write_text("# Accepted dossier\n", encoding="utf-8")
            jobs = root / "jobs" / "episode-capsules.jsonl"
            jobs.parent.mkdir(parents=True)
            jobs.write_text('{"job_id": "group-002-capsule"}\n', encoding="utf-8")
            write_status(root / "course" / "production-status.csv")
            calls: list[tuple[str, str, str]] = []

            def fake_run_job(manifest_path: Path, job_id: str, agent: str, **kwargs):
                calls.append((manifest_path.name, job_id, agent))
                capsule_path = root / "course" / "episode_capsules" / "group-002.json"
                capsule_path.parent.mkdir(parents=True, exist_ok=True)
                capsule_path.write_text(json.dumps(make_capsule(root), indent=2), encoding="utf-8")
                return [agent, job_id]

            with patch("consciousness_pipeline.episodes.acceptance.run_job", side_effect=fake_run_job):
                result = accept_episode("group-002", "codex", root=root)

            self.assertEqual(result, [["codex", "group-002-capsule"]])
            self.assertEqual(calls, [("episode-capsules.jsonl", "group-002-capsule", "codex")])
            callback_index = json.loads((root / "course" / "callback_index.json").read_text(encoding="utf-8"))
            self.assertIn("hard_problem", callback_index)
            with (root / "course" / "production-status.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["script_status"], "source_script_ready")
            self.assertEqual(rows[0]["notebooklm_status"], "notebooklm_bundle_ready")
            self.assertIn("capsule generated", rows[0]["message"])

    def test_accept_episode_refuses_missing_dossier_before_running_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "jobs").mkdir()
            (root / "jobs" / "episode-capsules.jsonl").write_text('{"job_id": "group-002-capsule"}\n')

            with patch("consciousness_pipeline.episodes.acceptance.run_job") as run_job:
                with self.assertRaises(EpisodeAcceptanceError) as context:
                    accept_episode("group-002", "codex", root=root)

            self.assertIn("research_dossier.md is missing", str(context.exception))
            run_job.assert_not_called()


if __name__ == "__main__":
    unittest.main()
