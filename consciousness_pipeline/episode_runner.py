import argparse
import json
from pathlib import Path
from typing import Any

from consciousness_pipeline.agent_runner import run_job
from consciousness_pipeline.config import PROJECT_ROOT
from consciousness_pipeline.course_context import write_episode_course_context
from consciousness_pipeline.course_context_selection import validate_course_context_selection
from consciousness_pipeline.episode_acceptance import accept_episode
from consciousness_pipeline.episode_reviews import validate_episode_review
from consciousness_pipeline.evaluations import EvaluationStage, evaluate_episode
from consciousness_pipeline.models import Section
from consciousness_pipeline.research import write_notebooklm_research_sources

RESEARCH_COMPLETENESS_FIELDS = ("core_claim", "strongest_case", "best_objections", "credibility")
PLACEHOLDER_MARKER = "research incomplete"
REQUIRED_DOSSIER_HEADINGS = (
    "## Episode Metadata",
    "## Course Continuity Grounding",
    "## Source Notes And Local Input Paths",
)


class ResearchReadinessError(RuntimeError):
    pass


class SourceDossierReadinessError(RuntimeError):
    pass


class EpisodeReviewGateError(RuntimeError):
    pass


class EpisodeEvaluationGateError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _episode_manifest_path(root: Path, episode_id: str) -> Path:
    return root / "episodes" / episode_id / "manifest.json"


def _research_manifest_path(root: Path) -> Path:
    return root / "jobs" / "research.jsonl"


def _source_script_manifest_path(root: Path) -> Path:
    return root / "jobs" / "source-scripts.jsonl"


def _context_selection_manifest_path(root: Path) -> Path:
    return root / "jobs" / "course-context-selections.jsonl"


def _context_selection_output_path(root: Path, episode_id: str) -> Path:
    return root / "episodes" / episode_id / "context_selection.json"


def _episode_review_manifest_path(root: Path) -> Path:
    return root / "jobs" / "episode-reviews.jsonl"


def _section_ids(manifest: dict[str, Any]) -> list[str]:
    return [str(section_id) for section_id in manifest["section_ids"]]


def _script_job_id(manifest: dict[str, Any], episode_id: str) -> str:
    return str(manifest.get("script_job_id", f"{episode_id}-script"))


def _review_job_id(episode_id: str) -> str:
    return f"{episode_id}-review"


def _script_output_path(root: Path, manifest: dict[str, Any], episode_id: str) -> Path:
    path = Path(str(manifest.get("script_output", f"episodes/{episode_id}/script.json")))
    return path if path.is_absolute() else root / path


def _bundle_output_path(root: Path, manifest: dict[str, Any], episode_id: str) -> Path:
    path = Path(str(manifest.get("bundle_output_path", f"episodes/{episode_id}/notebooklm_bundle/research_dossier.md")))
    return path if path.is_absolute() else root / path


def _review_output_path(root: Path, episode_id: str) -> Path:
    return root / "episodes" / episode_id / "review.json"


def _is_placeholder(value: object) -> bool:
    return isinstance(value, str) and PLACEHOLDER_MARKER in value.casefold()


def _raise_evaluation_errors(root: Path, episode_id: str, stage: EvaluationStage) -> None:
    report = evaluate_episode(root, episode_id, stage=stage)
    summary = report.get("summary", {})
    error_count = int(summary.get("errors", 0)) if isinstance(summary, dict) else 0
    if error_count == 0:
        return
    issues = report.get("issues", [])
    detail_lines: list[str] = []
    if isinstance(issues, list):
        for issue in issues:
            if not isinstance(issue, dict) or issue.get("severity") != "error":
                continue
            path = f" ({issue['path']})" if issue.get("path") else ""
            detail_lines.append(f"{issue.get('check_id')}: {issue.get('message')}{path}")
    detail = "\n- ".join(detail_lines)
    raise EpisodeEvaluationGateError(f"{episode_id} failed {stage} evaluation:\n- {detail}")


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


def write_episode_context(
    root: Path,
    episode_id: str,
    manifest: dict[str, Any],
    selection_path: Path | None = None,
) -> Path:
    return write_episode_course_context(root, episode_id, selection_path=selection_path)


def select_episode_context(
    episode_id: str,
    agent: str,
    root: Path = PROJECT_ROOT,
    dry_run: bool = False,
) -> list[str]:
    command = run_job(
        _context_selection_manifest_path(root),
        f"{episode_id}-context-selection",
        agent,
        root=root,
        dry_run=dry_run,
    )
    if dry_run:
        return command
    selection_path = _context_selection_output_path(root, episode_id)
    if not selection_path.exists():
        raise RuntimeError(f"{selection_path.relative_to(root)} was not written by the context selection job")
    validate_course_context_selection(_read_json(selection_path), root=root)
    write_episode_course_context(root, episode_id, selection_path=selection_path)
    return command


def validate_source_dossier_ready(root: Path, episode_id: str, manifest: dict[str, Any]) -> None:
    errors: list[str] = []
    script_path = _script_output_path(root, manifest, episode_id)
    dossier_path = _bundle_output_path(root, manifest, episode_id)
    script: dict[str, Any] | None = None
    if not script_path.exists():
        errors.append(f"{script_path.relative_to(root)} is missing")
    else:
        try:
            script = _read_json(script_path)
        except json.JSONDecodeError as error:
            errors.append(f"{script_path.relative_to(root)} is not valid JSON: {error}")
    if script is not None:
        if script.get("episode_id") != episode_id:
            errors.append(f"{script_path.relative_to(root)} has wrong episode_id")
        if script.get("missing_inputs") != []:
            errors.append(f"{script_path.relative_to(root)} has non-empty missing_inputs")
        if not isinstance(script.get("research_dossier_markdown"), str) or not script[
            "research_dossier_markdown"
        ].strip():
            errors.append(f"{script_path.relative_to(root)} has empty research_dossier_markdown")
        if not isinstance(script.get("citations"), list) or not script["citations"]:
            errors.append(f"{script_path.relative_to(root)} has no citations")
    if not dossier_path.exists():
        errors.append(f"{dossier_path.relative_to(root)} is missing")
    else:
        dossier = dossier_path.read_text(encoding="utf-8")
        if not dossier.strip():
            errors.append(f"{dossier_path.relative_to(root)} is empty")
        for heading in REQUIRED_DOSSIER_HEADINGS:
            if heading not in dossier:
                errors.append(f"{dossier_path.relative_to(root)} is missing `{heading}`")
    if errors:
        detail = "\n- ".join(errors)
        raise SourceDossierReadinessError(f"Source dossier is not production-ready:\n- {detail}")


def bundle_episode_sources(root: Path, episode_id: str, manifest: dict[str, Any]) -> list[Path]:
    sections_path = root / "data" / "extracted" / "sections.json"
    sections = [Section.from_dict(item) for item in json.loads(sections_path.read_text(encoding="utf-8"))]
    bundle_dir = Path(str(manifest.get("notebooklm_bundle_dir", f"episodes/{episode_id}/notebooklm_bundle")))
    if not bundle_dir.is_absolute():
        bundle_dir = root / bundle_dir
    return write_notebooklm_research_sources(
        sections=sections,
        section_ids=tuple(_section_ids(manifest)),
        research_dir=root / "data" / "research",
        output_dir=bundle_dir / "sources",
    )


def review_episode(root: Path, episode_id: str, review_agent: str) -> list[str]:
    command = run_job(_episode_review_manifest_path(root), _review_job_id(episode_id), review_agent, root=root)
    review_path = _review_output_path(root, episode_id)
    if not review_path.exists():
        raise EpisodeReviewGateError(f"{review_path.relative_to(root)} was not written by the review job")
    review = _read_json(review_path)
    validate_episode_review(review, episode_id=episode_id)
    if not review["approved"]:
        issues = "; ".join(str(issue) for issue in review["blocking_issues"])
        raise EpisodeReviewGateError(f"review rejected {episode_id}: {issues}")
    return command


def plan_episode_jobs(
    episode_id: str,
    root: Path = PROJECT_ROOT,
    auto_accept: bool = False,
) -> list[dict[str, str]]:
    manifest = _read_json(_episode_manifest_path(root, episode_id))
    research_manifest = _research_manifest_path(root)
    source_script_manifest = _source_script_manifest_path(root)
    plan = [
        {
            "kind": "course_context_selection",
            "manifest": str(_context_selection_manifest_path(root)),
            "job_id": f"{episode_id}-context-selection",
        },
    ]
    plan.extend(
        {"kind": "research", "manifest": str(research_manifest), "job_id": f"research-{section_id}"}
        for section_id in _section_ids(manifest)
    )
    plan.append(
        {
            "kind": "source_script",
            "manifest": str(source_script_manifest),
            "job_id": _script_job_id(manifest, episode_id),
        }
    )
    if auto_accept:
        plan.append(
            {
                "kind": "episode_review",
                "manifest": str(_episode_review_manifest_path(root)),
                "job_id": _review_job_id(episode_id),
            }
        )
        plan.append(
            {
                "kind": "course_episode_capsule",
                "manifest": str(root / "jobs" / "episode-capsules.jsonl"),
                "job_id": f"{episode_id}-capsule",
            }
        )
    return plan


def run_episode(
    episode_id: str,
    agent: str,
    root: Path = PROJECT_ROOT,
    dry_run: bool = False,
    auto_accept: bool = False,
    review_agent: str | None = None,
) -> list[list[str]]:
    manifest = _read_json(_episode_manifest_path(root, episode_id))
    section_ids = _section_ids(manifest)
    if auto_accept and review_agent is None:
        review_agent = "claude"
    if dry_run:
        return [[step["manifest"], step["job_id"]] for step in plan_episode_jobs(episode_id, root, auto_accept)]

    commands: list[list[str]] = []
    commands.append(select_episode_context(episode_id, agent, root=root))
    _raise_evaluation_errors(root, episode_id, "context")
    research_manifest = _research_manifest_path(root)
    for section_id in section_ids:
        commands.append(run_job(research_manifest, f"research-{section_id}", agent, root=root))

    validate_research_ready(root, section_ids)
    _raise_evaluation_errors(root, episode_id, "research")
    commands.append(
        run_job(
            _source_script_manifest_path(root),
            _script_job_id(manifest, episode_id),
            agent,
            root=root,
        )
    )
    validate_source_dossier_ready(root, episode_id, manifest)
    _raise_evaluation_errors(root, episode_id, "dossier")
    if auto_accept:
        bundle_episode_sources(root, episode_id, manifest)
        _raise_evaluation_errors(root, episode_id, "bundle")
        commands.append(review_episode(root, episode_id, str(review_agent)))
        commands.extend(accept_episode(episode_id, str(review_agent), root=root))
        _raise_evaluation_errors(root, episode_id, "accepted")
    return commands


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one episode through the required production order")
    parser.add_argument("--episode-id", required=True, help="Episode id, e.g. group-003")
    parser.add_argument("--agent", required=True, choices=("codex", "claude"), help="Headless agent backend")
    parser.add_argument("--dry-run", action="store_true", help="Print the job order without executing jobs")
    parser.add_argument("--auto-accept", action="store_true", help="Review and accept the dossier after generation")
    parser.add_argument(
        "--review-agent",
        choices=("codex", "claude"),
        help="Agent backend used for the auto-accept review and capsule job; defaults to claude",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_episode(
        args.episode_id,
        args.agent,
        dry_run=args.dry_run,
        auto_accept=args.auto_accept,
        review_agent=args.review_agent,
    )
    if args.dry_run:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
