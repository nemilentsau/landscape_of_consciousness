import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from consciousness_pipeline.episode_runner import ResearchReadinessError, run_episode

READY_DOSSIER = "## Episode Metadata\n\n## Course Continuity Grounding\n\n## Source Notes And Local Input Paths\n"


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _complete_research(section_id: str) -> dict[str, object]:
    return {
        "section_id": section_id,
        "opening_question": f"What is the strongest case for section {section_id}?",
        "core_claim": f"Substantive core claim for section {section_id}.",
        "strongest_case": f"Substantive strongest case for section {section_id}.",
        "best_objections": f"Substantive objections for section {section_id}.",
        "credibility": "Active debate with named sources.",
        "listener_hooks": ["A useful listener hook."],
        "sources": [
            {"kind": "primary", "title": "A landscape of consciousness", "url": "", "citation": "Kuhn 2024"},
            {"kind": "review", "title": "External review", "url": "https://example.com", "citation": "Example 2024"},
        ],
    }


def _context_selection(episode_id: str) -> dict[str, object]:
    return {
        "schema_version": "course_context_selection_v1",
        "episode_id": episode_id,
        "selected_capsules": [],
        "selected_callbacks": [],
        "rejected_near_misses": [],
    }


class EpisodeRunnerTest(unittest.TestCase):
    def test_run_episode_refuses_script_when_research_is_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_json(
                root / "episodes" / "group-003" / "manifest.json",
                {
                    "episode_id": "group-003",
                    "title": "Top-level sections Part 3",
                    "episode_question": "What is the strongest case for this cluster, and where does it break?",
                    "section_ids": ["11", "12"],
                    "script_job_id": "group-003-script",
                },
            )
            _write_jsonl(root / "jobs" / "course-context-selections.jsonl", [{"job_id": "group-003-context-selection"}])
            _write_jsonl(
                root / "jobs" / "research.jsonl",
                [{"job_id": "research-11"}, {"job_id": "research-12"}],
            )
            _write_jsonl(root / "jobs" / "source-scripts.jsonl", [{"job_id": "group-003-script"}])
            _write_json(
                root / "data" / "research" / "11.json",
                {
                    "section_id": "11",
                    "core_claim": "Research incomplete: use Kuhn's section text as the starting point for this claim.",
                    "strongest_case": "Research incomplete: add the strongest academic case before upload.",
                    "best_objections": "Research incomplete: add at least one serious objection before upload.",
                    "credibility": "Research incomplete",
                    "sources": [
                        {"kind": "primary", "title": "A landscape of consciousness", "url": "", "citation": "Kuhn 2024"}
                    ],
                },
            )
            _write_json(root / "data" / "research" / "12.json", _complete_research("12"))

            calls: list[tuple[str, str]] = []

            def fake_run_job(manifest_path: Path, job_id: str, agent: str, **kwargs):
                calls.append((manifest_path.name, job_id))
                if job_id == "group-003-context-selection":
                    _write_json(
                        root / "episodes" / "group-003" / "context_selection.json",
                        _context_selection("group-003"),
                    )
                return [agent, job_id]

            with patch("consciousness_pipeline.episode_runner.run_job", side_effect=fake_run_job):
                with self.assertRaises(ResearchReadinessError) as context:
                    run_episode("group-003", "codex", root=root)

            self.assertIn("data/research/11.json", str(context.exception))
            self.assertEqual(
                calls,
                [
                    ("course-context-selections.jsonl", "group-003-context-selection"),
                    ("research.jsonl", "research-11"),
                    ("research.jsonl", "research-12"),
                ],
            )

    def test_run_episode_runs_research_then_script_after_research_is_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_json(
                root / "episodes" / "group-003" / "manifest.json",
                {
                    "episode_id": "group-003",
                    "title": "Top-level sections Part 3",
                    "episode_question": "What is the strongest case for this cluster, and where does it break?",
                    "section_ids": ["11", "12"],
                    "script_job_id": "group-003-script",
                },
            )
            _write_jsonl(root / "jobs" / "course-context-selections.jsonl", [{"job_id": "group-003-context-selection"}])
            _write_jsonl(root / "jobs" / "research.jsonl", [{"job_id": "research-11"}, {"job_id": "research-12"}])
            _write_jsonl(root / "jobs" / "source-scripts.jsonl", [{"job_id": "group-003-script"}])
            _write_json(root / "data" / "research" / "11.json", _complete_research("11"))
            _write_json(root / "data" / "research" / "12.json", _complete_research("12"))

            calls: list[tuple[str, str]] = []

            def fake_run_job(manifest_path: Path, job_id: str, agent: str, **kwargs):
                calls.append((manifest_path.name, job_id))
                if job_id == "group-003-context-selection":
                    _write_json(
                        root / "episodes" / "group-003" / "context_selection.json",
                        _context_selection("group-003"),
                    )
                return [agent, job_id]

            with patch("consciousness_pipeline.episode_runner.run_job", side_effect=fake_run_job):
                run_episode("group-003", "codex", root=root)

            self.assertEqual(
                calls,
                [
                    ("course-context-selections.jsonl", "group-003-context-selection"),
                    ("research.jsonl", "research-11"),
                    ("research.jsonl", "research-12"),
                    ("source-scripts.jsonl", "group-003-script"),
                ],
            )

    def test_run_episode_auto_accepts_only_after_review_agent_approves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            section = {
                "section_id": "11",
                "title": "Quantum theories",
                "level": 1,
                "start_page": 61,
                "end_page": 61,
                "taxonomy_path": ["Quantum theories"],
                "text": "Quantum theories section text.",
                "slug": "11-quantum-theories",
            }
            _write_json(root / "data" / "extracted" / "sections.json", [section])
            _write_json(
                root / "episodes" / "group-003" / "manifest.json",
                {
                    "episode_id": "group-003",
                    "title": "Top-level sections Part 3",
                    "episode_question": "What is the strongest case for this cluster, and where does it break?",
                    "section_ids": ["11"],
                    "script_job_id": "group-003-script",
                    "notebooklm_bundle_dir": "episodes/group-003/notebooklm_bundle",
                },
            )
            _write_jsonl(root / "jobs" / "course-context-selections.jsonl", [{"job_id": "group-003-context-selection"}])
            _write_jsonl(root / "jobs" / "research.jsonl", [{"job_id": "research-11"}])
            _write_jsonl(root / "jobs" / "source-scripts.jsonl", [{"job_id": "group-003-script"}])
            _write_jsonl(root / "jobs" / "episode-reviews.jsonl", [{"job_id": "group-003-review"}])
            _write_json(root / "data" / "research" / "11.json", _complete_research("11"))

            calls: list[tuple[str, str, str]] = []
            accepted: list[tuple[str, str]] = []

            def fake_run_job(manifest_path: Path, job_id: str, agent: str, **kwargs):
                calls.append((manifest_path.name, job_id, agent))
                if job_id == "group-003-context-selection":
                    _write_json(
                        root / "episodes" / "group-003" / "context_selection.json",
                        _context_selection("group-003"),
                    )
                if job_id == "group-003-script":
                    _write_json(
                        root / "episodes" / "group-003" / "script.json",
                        {
                            "episode_id": "group-003",
                            "title": "Top-level sections Part 3",
                            "episode_question": "What is the strongest case for this cluster, and where does it break?",
                            "duration_target": "long_form",
                            "research_dossier_markdown": READY_DOSSIER,
                            "citations": ["Kuhn 2024", "Atmanspacher 2024"],
                            "missing_inputs": [],
                        },
                    )
                    dossier = root / "episodes" / "group-003" / "notebooklm_bundle" / "research_dossier.md"
                    dossier.parent.mkdir(parents=True, exist_ok=True)
                    dossier.write_text(READY_DOSSIER, encoding="utf-8")
                if job_id == "group-003-review":
                    _write_json(
                        root / "episodes" / "group-003" / "review.json",
                        {
                            "schema_version": "episode_review_v1",
                            "episode_id": "group-003",
                            "approved": True,
                            "summary": "The dossier is suitable for continuity.",
                            "blocking_issues": [],
                            "non_blocking_notes": ["Minor editorial polish can wait."],
                            "checked_items": ["no missing inputs", "not a dialogue script"],
                        },
                    )
                return [agent, job_id]

            def fake_accept_episode(episode_id: str, agent: str, **kwargs):
                accepted.append((episode_id, agent))
                return [[agent, f"{episode_id}-capsule"]]

            with patch("consciousness_pipeline.episode_runner.run_job", side_effect=fake_run_job), patch(
                "consciousness_pipeline.episode_runner.accept_episode", side_effect=fake_accept_episode
            ):
                run_episode("group-003", "codex", root=root, auto_accept=True, review_agent="claude")

            self.assertEqual(
                calls,
                [
                    ("course-context-selections.jsonl", "group-003-context-selection", "codex"),
                    ("research.jsonl", "research-11", "codex"),
                    ("source-scripts.jsonl", "group-003-script", "codex"),
                    ("episode-reviews.jsonl", "group-003-review", "claude"),
                ],
            )
            self.assertEqual(accepted, [("group-003", "claude")])
            self.assertTrue(
                (
                    root
                    / "episodes"
                    / "group-003"
                    / "notebooklm_bundle"
                    / "sources"
                    / "11-quantum-theories.md"
                ).exists()
            )

    def test_run_episode_auto_accept_stops_when_review_agent_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            section = {
                "section_id": "11",
                "title": "Quantum theories",
                "level": 1,
                "start_page": 61,
                "end_page": 61,
                "taxonomy_path": ["Quantum theories"],
                "text": "Quantum theories section text.",
                "slug": "11-quantum-theories",
            }
            _write_json(root / "data" / "extracted" / "sections.json", [section])
            _write_json(
                root / "episodes" / "group-003" / "manifest.json",
                {
                    "episode_id": "group-003",
                    "title": "Top-level sections Part 3",
                    "episode_question": "What is the strongest case for this cluster, and where does it break?",
                    "section_ids": ["11"],
                    "script_job_id": "group-003-script",
                    "notebooklm_bundle_dir": "episodes/group-003/notebooklm_bundle",
                },
            )
            _write_jsonl(root / "jobs" / "course-context-selections.jsonl", [{"job_id": "group-003-context-selection"}])
            _write_jsonl(root / "jobs" / "research.jsonl", [{"job_id": "research-11"}])
            _write_jsonl(root / "jobs" / "source-scripts.jsonl", [{"job_id": "group-003-script"}])
            _write_jsonl(root / "jobs" / "episode-reviews.jsonl", [{"job_id": "group-003-review"}])
            _write_json(root / "data" / "research" / "11.json", _complete_research("11"))

            def fake_run_job(manifest_path: Path, job_id: str, agent: str, **kwargs):
                if job_id == "group-003-context-selection":
                    _write_json(
                        root / "episodes" / "group-003" / "context_selection.json",
                        _context_selection("group-003"),
                    )
                if job_id == "group-003-script":
                    _write_json(
                        root / "episodes" / "group-003" / "script.json",
                        {
                            "episode_id": "group-003",
                            "title": "Top-level sections Part 3",
                            "episode_question": "What is the strongest case for this cluster, and where does it break?",
                            "duration_target": "long_form",
                            "research_dossier_markdown": READY_DOSSIER,
                            "citations": ["Kuhn 2024", "Atmanspacher 2024"],
                            "missing_inputs": [],
                        },
                    )
                    dossier = root / "episodes" / "group-003" / "notebooklm_bundle" / "research_dossier.md"
                    dossier.parent.mkdir(parents=True, exist_ok=True)
                    dossier.write_text(READY_DOSSIER, encoding="utf-8")
                if job_id == "group-003-review":
                    _write_json(
                        root / "episodes" / "group-003" / "review.json",
                        {
                            "schema_version": "episode_review_v1",
                            "episode_id": "group-003",
                            "approved": False,
                            "summary": "The dossier needs repair.",
                            "blocking_issues": ["The dossier includes host dialogue."],
                            "non_blocking_notes": [],
                            "checked_items": ["dialogue/script format"],
                        },
                    )
                return [agent, job_id]

            with patch("consciousness_pipeline.episode_runner.run_job", side_effect=fake_run_job), patch(
                "consciousness_pipeline.episode_runner.accept_episode"
            ) as accept_episode:
                with self.assertRaises(RuntimeError) as context:
                    run_episode("group-003", "codex", root=root, auto_accept=True, review_agent="claude")

            self.assertIn("review rejected group-003", str(context.exception))
            self.assertIn("host dialogue", str(context.exception))
            accept_episode.assert_not_called()


if __name__ == "__main__":
    unittest.main()
