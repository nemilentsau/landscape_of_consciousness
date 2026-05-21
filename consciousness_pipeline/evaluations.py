import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from consciousness_pipeline.episode_capsules import EpisodeCapsuleValidationError, validate_episode_capsule

EvaluationSeverity = Literal["error", "warning"]
EvaluationStage = Literal["context", "research", "dossier", "bundle", "accepted"]

STAGE_RANK: dict[EvaluationStage, int] = {
    "context": 1,
    "research": 2,
    "dossier": 3,
    "bundle": 4,
    "accepted": 5,
}

RESEARCH_COMPLETENESS_FIELDS = ("core_claim", "strongest_case", "best_objections", "credibility")
PLACEHOLDER_MARKER = "research incomplete"
REQUIRED_DOSSIER_HEADINGS = (
    "## Episode Metadata",
    "## Course Continuity Grounding",
    "## Source Notes And Local Input Paths",
)
REQUIRED_SOURCE_HEADINGS = (
    "## Kuhn Review Anchor",
    "## Research Question",
    "## Core Claim",
    "## Strongest Case",
    "## Best Objections And Limits",
    "## Credibility / Epistemic Status",
    "## Sources",
)
PERFORMED_SCRIPT_LINE = re.compile(r"^\s*(host|speaker\s*\d+|narrator)\s*:", re.IGNORECASE | re.MULTILINE)


@dataclass(frozen=True)
class EvaluationIssue:
    check_id: str
    severity: EvaluationSeverity
    message: str
    path: str | None = None
    value: int | str | None = None
    limit: int | str | None = None

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "check_id": self.check_id,
            "severity": self.severity,
            "message": self.message,
        }
        if self.path is not None:
            result["path"] = self.path
        if self.value is not None:
            result["value"] = self.value
        if self.limit is not None:
            result["limit"] = self.limit
        return result


@dataclass(frozen=True)
class EpisodeEvaluationConfig:
    context_word_limit: int = 1500
    synthesis_context_word_limit: int = 2500
    research_field_word_min: int = 5
    research_sources_min: int = 2
    dossier_word_min_per_section: int = 250
    source_word_min: int = 120
    durable_concepts_limit: int = 10
    recurring_distinctions_limit: int = 7
    do_not_reexplain_limit: int = 7
    open_tensions_limit: int = 8
    callbacks_limit: int = 7
    callback_family_repeat_limit: int = 2


def _relative_project_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _word_count(path: Path) -> int:
    return len(_read_text(path).split())


def _should_check(stage: EvaluationStage, required: EvaluationStage) -> bool:
    return STAGE_RANK[stage] >= STAGE_RANK[required]


def _issue(
    issues: list[EvaluationIssue],
    check_id: str,
    severity: EvaluationSeverity,
    message: str,
    path: Path | None = None,
    root: Path | None = None,
    value: int | str | None = None,
    limit: int | str | None = None,
) -> None:
    issue_path = _relative_project_path(root, path) if root is not None and path is not None else None
    issues.append(
        EvaluationIssue(
            check_id=check_id,
            severity=severity,
            message=message,
            path=issue_path,
            value=value,
            limit=limit,
        )
    )


def _section_count(manifest: dict[str, Any]) -> int:
    section_ids = manifest.get("section_ids")
    if isinstance(section_ids, list):
        return len(section_ids)
    sections = manifest.get("sections")
    if isinstance(sections, list):
        return len(sections)
    return 0


def _section_ids(manifest: dict[str, Any]) -> list[str]:
    section_ids = manifest.get("section_ids")
    if isinstance(section_ids, list):
        return [str(section_id) for section_id in section_ids]
    sections = manifest.get("sections")
    if isinstance(sections, list):
        return [
            str(section["section_id"])
            for section in sections
            if isinstance(section, dict) and "section_id" in section
        ]
    return []


def _section_titles(manifest: dict[str, Any]) -> list[str]:
    sections = manifest.get("sections")
    if not isinstance(sections, list):
        return []
    return [str(section["title"]) for section in sections if isinstance(section, dict) and "title" in section]


def _is_synthesis_episode(manifest: dict[str, Any]) -> bool:
    text_parts = [str(manifest.get("title", ""))]
    for section in manifest.get("sections", []):
        if isinstance(section, dict):
            text_parts.append(str(section.get("title", "")))
    text = " ".join(text_parts).casefold()
    return any(marker in text for marker in ("reflection", "reflections", "synthesis", "recap"))


def _evaluate_context(
    root: Path,
    episode_id: str,
    manifest: dict[str, Any],
    config: EpisodeEvaluationConfig,
    issues: list[EvaluationIssue],
) -> None:
    context_path = root / "episodes" / episode_id / "course_context.md"
    if not context_path.exists():
        _issue(issues, "context_missing", "error", "Course context is missing", context_path, root)
        return
    limit = config.synthesis_context_word_limit if _is_synthesis_episode(manifest) else config.context_word_limit
    words = _word_count(context_path)
    if words > limit:
        _issue(
            issues,
            "context_word_budget",
            "warning",
            "Course context exceeds the working-memory word budget",
            context_path,
            root,
            value=words,
            limit=limit,
        )


def _script_output_path(root: Path, episode_id: str, manifest: dict[str, Any]) -> Path:
    path = Path(str(manifest.get("script_output", f"episodes/{episode_id}/script.json")))
    return path if path.is_absolute() else root / path


def _bundle_output_path(root: Path, episode_id: str, manifest: dict[str, Any]) -> Path:
    path = Path(str(manifest.get("bundle_output_path", f"episodes/{episode_id}/notebooklm_bundle/research_dossier.md")))
    return path if path.is_absolute() else root / path


def _is_placeholder(value: object) -> bool:
    return isinstance(value, str) and PLACEHOLDER_MARKER in value.casefold()


def _evaluate_research_records(
    root: Path,
    manifest: dict[str, Any],
    config: EpisodeEvaluationConfig,
    issues: list[EvaluationIssue],
) -> None:
    for section_id in _section_ids(manifest):
        research_path = root / "data" / "research" / f"{section_id}.json"
        if not research_path.exists():
            _issue(issues, "research_missing", "error", "Section research record is missing", research_path, root)
            continue
        try:
            record = _read_json(research_path)
        except json.JSONDecodeError as error:
            _issue(
                issues,
                "research_invalid",
                "error",
                f"Research record is invalid JSON: {error}",
                research_path,
                root,
            )
            continue
        if str(record.get("section_id")) != section_id:
            _issue(
                issues,
                "research_section_mismatch",
                "error",
                "Research record section_id does not match the manifest section",
                research_path,
                root,
                value=str(record.get("section_id")),
                limit=section_id,
            )
        for field in RESEARCH_COMPLETENESS_FIELDS:
            value = record.get(field)
            if not isinstance(value, str) or not value.strip() or _is_placeholder(value):
                _issue(
                    issues,
                    "research_field_incomplete",
                    "error",
                    f"Research record has incomplete field `{field}`",
                    research_path,
                    root,
                )
                continue
            words = len(value.split())
            if words < config.research_field_word_min:
                _issue(
                    issues,
                    "research_field_thin",
                    "warning",
                    f"Research field `{field}` is very short",
                    research_path,
                    root,
                    value=words,
                    limit=config.research_field_word_min,
                )
        sources = record.get("sources")
        if not isinstance(sources, list) or not sources:
            _issue(issues, "research_sources_missing", "error", "Research record has no sources", research_path, root)
        elif len(sources) < config.research_sources_min:
            _issue(
                issues,
                "research_sources_thin",
                "warning",
                "Research record has fewer sources than the advisory minimum",
                research_path,
                root,
                value=len(sources),
                limit=config.research_sources_min,
            )


def _evaluate_script_json(
    root: Path,
    episode_id: str,
    manifest: dict[str, Any],
    config: EpisodeEvaluationConfig,
    issues: list[EvaluationIssue],
) -> dict[str, Any] | None:
    script_path = _script_output_path(root, episode_id, manifest)
    if not script_path.exists():
        _issue(issues, "script_missing", "error", "Source dossier JSON output is missing", script_path, root)
        return None
    try:
        script = _read_json(script_path)
    except json.JSONDecodeError as error:
        _issue(issues, "script_invalid", "error", f"Source dossier JSON is invalid: {error}", script_path, root)
        return None
    if script.get("episode_id") != episode_id:
        _issue(
            issues,
            "script_episode_mismatch",
            "error",
            "Source dossier JSON has wrong episode_id",
            script_path,
            root,
        )
    missing_inputs = script.get("missing_inputs")
    if missing_inputs != []:
        _issue(
            issues,
            "script_missing_inputs",
            "error",
            "Source dossier JSON reports missing inputs",
            script_path,
            root,
            value=json.dumps(missing_inputs, ensure_ascii=False),
        )
    dossier_markdown = script.get("research_dossier_markdown")
    if not isinstance(dossier_markdown, str) or not dossier_markdown.strip():
        _issue(
            issues,
            "script_dossier_empty",
            "error",
            "Source dossier JSON has empty research_dossier_markdown",
            script_path,
            root,
        )
    elif PERFORMED_SCRIPT_LINE.search(dossier_markdown):
        _issue(
            issues,
            "script_performed_dialogue",
            "error",
            "Source dossier JSON appears to contain performed dialogue instead of source material",
            script_path,
            root,
        )
    citations = script.get("citations")
    if not isinstance(citations, list) or not citations:
        _issue(issues, "script_citations_missing", "error", "Source dossier JSON has no citations", script_path, root)
    elif len(citations) < max(1, _section_count(manifest)):
        _issue(
            issues,
            "script_citations_thin",
            "warning",
            "Source dossier JSON has fewer citations than episode sections",
            script_path,
            root,
            value=len(citations),
            limit=max(1, _section_count(manifest)),
        )
    if isinstance(dossier_markdown, str):
        words = len(dossier_markdown.split())
        limit = max(
            config.dossier_word_min_per_section,
            config.dossier_word_min_per_section * max(1, _section_count(manifest)),
        )
        if words < limit:
            _issue(
                issues,
                "script_dossier_thin",
                "warning",
                "Source dossier JSON markdown is below the advisory substance floor",
                script_path,
                root,
                value=words,
                limit=limit,
            )
    return script


def _evaluate_dossier_markdown(
    root: Path,
    episode_id: str,
    manifest: dict[str, Any],
    script: dict[str, Any] | None,
    issues: list[EvaluationIssue],
) -> None:
    dossier_path = _bundle_output_path(root, episode_id, manifest)
    if not dossier_path.exists():
        _issue(issues, "dossier_missing", "error", "NotebookLM dossier markdown is missing", dossier_path, root)
        return
    dossier = _read_text(dossier_path)
    if not dossier.strip():
        _issue(issues, "dossier_empty", "error", "NotebookLM dossier markdown is empty", dossier_path, root)
        return
    for heading in REQUIRED_DOSSIER_HEADINGS:
        if heading not in dossier:
            _issue(
                issues,
                "dossier_heading_missing",
                "error",
                "NotebookLM dossier markdown is missing a required heading",
                dossier_path,
                root,
                value=heading,
            )
    if PERFORMED_SCRIPT_LINE.search(dossier):
        _issue(
            issues,
            "dossier_performed_dialogue",
            "error",
            "NotebookLM dossier appears to contain performed dialogue instead of source material",
            dossier_path,
            root,
        )
    for title in _section_titles(manifest):
        if title not in dossier:
            _issue(
                issues,
                "dossier_section_title_missing",
                "warning",
                "NotebookLM dossier does not mention a manifest section title",
                dossier_path,
                root,
                value=title,
            )
    if script is not None and isinstance(script.get("research_dossier_markdown"), str):
        script_markdown = str(script["research_dossier_markdown"]).strip()
        if script_markdown and script_markdown != dossier.strip():
            _issue(
                issues,
                "dossier_script_mismatch",
                "warning",
                "NotebookLM dossier markdown differs from script.json research_dossier_markdown",
                dossier_path,
                root,
            )


def _evaluate_dossier(
    root: Path,
    episode_id: str,
    manifest: dict[str, Any],
    config: EpisodeEvaluationConfig,
    issues: list[EvaluationIssue],
) -> None:
    script = _evaluate_script_json(root, episode_id, manifest, config, issues)
    _evaluate_dossier_markdown(root, episode_id, manifest, script, issues)


def _evaluate_bundle(
    root: Path,
    episode_id: str,
    manifest: dict[str, Any],
    config: EpisodeEvaluationConfig,
    issues: list[EvaluationIssue],
) -> None:
    bundle_dir = root / "episodes" / episode_id / "notebooklm_bundle"
    dossier_path = bundle_dir / "research_dossier.md"
    sources_dir = bundle_dir / "sources"
    if not dossier_path.exists():
        _issue(issues, "bundle_dossier_missing", "error", "NotebookLM dossier is missing", dossier_path, root)
    if not sources_dir.exists():
        _issue(issues, "bundle_sources_missing", "error", "NotebookLM sources directory is missing", sources_dir, root)
        return
    source_paths = sorted(sources_dir.glob("*.md"))
    expected_sources = _section_count(manifest)
    if expected_sources and len(source_paths) != expected_sources:
        _issue(
            issues,
            "bundle_source_count",
            "error",
            "NotebookLM source count does not match episode section count",
            sources_dir,
            root,
            value=len(source_paths),
            limit=expected_sources,
        )
    for source_path in source_paths:
        source = _read_text(source_path)
        if PLACEHOLDER_MARKER in source.casefold():
            _issue(
                issues,
                "bundle_source_placeholder",
                "error",
                "NotebookLM source still contains placeholder research text",
                source_path,
                root,
            )
        for heading in REQUIRED_SOURCE_HEADINGS:
            if heading not in source:
                _issue(
                    issues,
                    "bundle_source_heading_missing",
                    "error",
                    "NotebookLM source is missing a required heading",
                    source_path,
                    root,
                    value=heading,
                )
        words = len(source.split())
        if words < config.source_word_min:
            _issue(
                issues,
                "bundle_source_thin",
                "warning",
                "NotebookLM source is below the advisory substance floor",
                source_path,
                root,
                value=words,
                limit=config.source_word_min,
            )


def _check_count(
    root: Path,
    path: Path,
    issues: list[EvaluationIssue],
    check_id: str,
    label: str,
    count: int,
    limit: int,
) -> None:
    if count > limit:
        _issue(
            issues,
            check_id,
            "warning",
            f"Episode capsule has too many {label}",
            path,
            root,
            value=count,
            limit=limit,
        )


def _evaluate_capsule(
    root: Path,
    episode_id: str,
    config: EpisodeEvaluationConfig,
    issues: list[EvaluationIssue],
) -> None:
    capsule_path = root / "course" / "episode_capsules" / f"{episode_id}.json"
    if not capsule_path.exists():
        _issue(issues, "capsule_missing", "error", "Accepted episode capsule is missing", capsule_path, root)
        return
    try:
        capsule = _read_json(capsule_path)
        validate_episode_capsule(capsule, root=root)
    except (json.JSONDecodeError, EpisodeCapsuleValidationError) as error:
        _issue(
            issues,
            "capsule_invalid",
            "error",
            f"Episode capsule is invalid: {error}",
            capsule_path,
            root,
        )
        return
    _check_count(
        root,
        capsule_path,
        issues,
        "capsule_durable_concepts_budget",
        "durable concepts",
        len(capsule.get("durable_concepts", [])),
        config.durable_concepts_limit,
    )
    _check_count(
        root,
        capsule_path,
        issues,
        "capsule_recurring_distinctions_budget",
        "recurring distinctions",
        len(capsule.get("recurring_distinctions", [])),
        config.recurring_distinctions_limit,
    )
    _check_count(
        root,
        capsule_path,
        issues,
        "capsule_do_not_reexplain_budget",
        "do-not-reexplain items",
        len(capsule.get("do_not_reexplain", [])),
        config.do_not_reexplain_limit,
    )
    _check_count(
        root,
        capsule_path,
        issues,
        "capsule_open_tensions_budget",
        "open tensions",
        len(capsule.get("open_tensions", [])),
        config.open_tensions_limit,
    )
    callbacks = capsule.get("callbacks", [])
    _check_count(
        root,
        capsule_path,
        issues,
        "capsule_callbacks_budget",
        "callbacks",
        len(callbacks),
        config.callbacks_limit,
    )
    family_counts: Counter[str] = Counter()
    for index, callback in enumerate(callbacks):
        if not isinstance(callback, dict):
            continue
        family = callback.get("family")
        tags = callback.get("tags")
        if not isinstance(family, str) or not family.strip():
            _issue(
                issues,
                "callback_family_missing",
                "warning",
                f"Callback {index} has no advisory family",
                capsule_path,
                root,
            )
        else:
            family_counts[family] += 1
        if not isinstance(tags, list) or not tags:
            _issue(
                issues,
                "callback_tags_missing",
                "warning",
                f"Callback {index} has no topic tags",
                capsule_path,
                root,
            )
    for family, count in sorted(family_counts.items()):
        if count > config.callback_family_repeat_limit:
            _issue(
                issues,
                "callback_family_concentration",
                "warning",
                "Callback family appears more often than the advisory diversity limit",
                capsule_path,
                root,
                value=f"{family}: {count}",
                limit=config.callback_family_repeat_limit,
            )


def _evaluate_callback_index(root: Path, episode_id: str, issues: list[EvaluationIssue]) -> None:
    capsule_path = root / "course" / "episode_capsules" / f"{episode_id}.json"
    index_path = root / "course" / "callback_index.json"
    if not capsule_path.exists() or not index_path.exists():
        return
    capsule = _read_json(capsule_path)
    callback_index = _read_json(index_path)
    for callback in capsule.get("callbacks", []):
        if not isinstance(callback, dict):
            continue
        concept = str(callback.get("concept", ""))
        entries = callback_index.get(concept)
        if not isinstance(entries, list):
            _issue(
                issues,
                "callback_index_missing_concept",
                "error",
                "Callback index is missing a capsule callback concept",
                index_path,
                root,
                value=concept,
            )
            continue
        matching_entries = [
            entry for entry in entries if isinstance(entry, dict) and entry.get("episode_id") == episode_id
        ]
        if not matching_entries:
            _issue(
                issues,
                "callback_index_missing_episode",
                "error",
                "Callback index is missing this episode's callback entry",
                index_path,
                root,
                value=concept,
            )


def evaluate_episode(
    root: Path,
    episode_id: str,
    stage: EvaluationStage = "accepted",
    config: EpisodeEvaluationConfig | None = None,
) -> dict[str, object]:
    config = config or EpisodeEvaluationConfig()
    issues: list[EvaluationIssue] = []
    manifest_path = root / "episodes" / episode_id / "manifest.json"
    if not manifest_path.exists():
        _issue(issues, "manifest_missing", "error", "Episode manifest is missing", manifest_path, root)
        manifest: dict[str, Any] = {}
    else:
        try:
            manifest = _read_json(manifest_path)
        except json.JSONDecodeError as error:
            _issue(
                issues,
                "manifest_invalid",
                "error",
                f"Episode manifest is invalid JSON: {error}",
                manifest_path,
                root,
            )
            manifest = {}
    if manifest:
        _evaluate_context(root, episode_id, manifest, config, issues)
        if _should_check(stage, "research"):
            _evaluate_research_records(root, manifest, config, issues)
        if _should_check(stage, "dossier"):
            _evaluate_dossier(root, episode_id, manifest, config, issues)
        if _should_check(stage, "bundle"):
            _evaluate_bundle(root, episode_id, manifest, config, issues)
        if _should_check(stage, "accepted"):
            _evaluate_capsule(root, episode_id, config, issues)
            _evaluate_callback_index(root, episode_id, issues)

    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    return {
        "episode_id": episode_id,
        "stage": stage,
        "ok": error_count == 0,
        "summary": {
            "errors": error_count,
            "warnings": warning_count,
            "issues": len(issues),
        },
        "issues": [issue.to_dict() for issue in issues],
    }
