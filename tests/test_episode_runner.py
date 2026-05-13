import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from consciousness_pipeline.episode_runner import ResearchReadinessError, run_episode


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


if __name__ == "__main__":
    unittest.main()
