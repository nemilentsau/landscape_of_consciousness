import argparse
import json
from pathlib import Path
from typing import Any

from consciousness_pipeline.agent_runner import run_job
from consciousness_pipeline.config import PROJECT_ROOT
from consciousness_pipeline.course_context import render_episode_course_context, write_initial_course_memory

RESEARCH_COMPLETENESS_FIELDS = ("core_claim", "strongest_case", "best_objections", "credibility")
PLACEHOLDER_MARKER = "research incomplete"


class ResearchReadinessError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _episode_manifest_path(root: Path, episode_id: str) -> Path:
    return root / "episodes" / episode_id / "manifest.json"


def _research_manifest_path(root: Path) -> Path:
    return root / "jobs" / "research.jsonl"


def _source_script_manifest_path(root: Path) -> Path:
    return root / "jobs" / "source-scripts.jsonl"


def _section_ids(manifest: dict[str, Any]) -> list[str]:
    return [str(section_id) for section_id in manifest["section_ids"]]


def _script_job_id(manifest: dict[str, Any], episode_id: str) -> str:
    return str(manifest.get("script_job_id", f"{episode_id}-script"))


def _is_placeholder(value: object) -> bool:
    return isinstance(value, str) and PLACEHOLDER_MARKER in value.casefold()


def validate_research_ready(root: Path, section_ids: list[str]) -> None:
    errors: list[str] = []
    for section_id in section_ids:
        research_path = root / "data" / "research" / f"{section_id}.json"
        if not research_path.exists():
            errors.append(f"{research_path.relative_to(root)} is missing")
            continue
        try:
            record = _read_json(research_path)
        except json.JSONDecodeError as error:
            errors.append(f"{research_path.relative_to(root)} is not valid JSON: {error}")
            continue
        for field in RESEARCH_COMPLETENESS_FIELDS:
            value = record.get(field)
            if not isinstance(value, str) or not value.strip() or _is_placeholder(value):
                errors.append(f"{research_path.relative_to(root)} has incomplete field `{field}`")
        sources = record.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{research_path.relative_to(root)} has no sources")
    if errors:
        detail = "\n- ".join(errors)
        raise ResearchReadinessError(f"Research records are not production-ready:\n- {detail}")


def write_episode_context(root: Path, episode_id: str, manifest: dict[str, Any]) -> Path:
    memory_path = root / "course" / "course_memory.md"
    if not memory_path.exists():
        write_initial_course_memory(memory_path)
    context_path = root / "episodes" / episode_id / "course_context.md"
    context_path.write_text(
        render_episode_course_context(manifest, memory_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    return context_path


def plan_episode_jobs(episode_id: str, root: Path = PROJECT_ROOT) -> list[dict[str, str]]:
    manifest = _read_json(_episode_manifest_path(root, episode_id))
    research_manifest = _research_manifest_path(root)
    source_script_manifest = _source_script_manifest_path(root)
    plan = [
        {"kind": "research", "manifest": str(research_manifest), "job_id": f"research-{section_id}"}
        for section_id in _section_ids(manifest)
    ]
    plan.append(
        {
            "kind": "source_script",
            "manifest": str(source_script_manifest),
            "job_id": _script_job_id(manifest, episode_id),
        }
    )
    return plan


def run_episode(
    episode_id: str,
    agent: str,
    root: Path = PROJECT_ROOT,
    dry_run: bool = False,
) -> list[list[str]]:
    manifest = _read_json(_episode_manifest_path(root, episode_id))
    section_ids = _section_ids(manifest)
    if dry_run:
        return [[step["manifest"], step["job_id"]] for step in plan_episode_jobs(episode_id, root)]

    write_episode_context(root, episode_id, manifest)
    commands: list[list[str]] = []
    research_manifest = _research_manifest_path(root)
    for section_id in section_ids:
        commands.append(run_job(research_manifest, f"research-{section_id}", agent, root=root))

    validate_research_ready(root, section_ids)
    commands.append(
        run_job(
            _source_script_manifest_path(root),
            _script_job_id(manifest, episode_id),
            agent,
            root=root,
        )
    )
    return commands


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one episode through the required production order")
    parser.add_argument("--episode-id", required=True, help="Episode id, e.g. group-003")
    parser.add_argument("--agent", required=True, choices=("codex", "claude"), help="Headless agent backend")
    parser.add_argument("--dry-run", action="store_true", help="Print the job order without executing jobs")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_episode(args.episode_id, args.agent, dry_run=args.dry_run)
    if args.dry_run:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
