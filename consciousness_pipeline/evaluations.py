import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from consciousness_pipeline.episode_capsules import EpisodeCapsuleValidationError, validate_episode_capsule

EvaluationSeverity = Literal["error", "warning"]
EvaluationStage = Literal["context", "bundle", "accepted"]

STAGE_RANK: dict[EvaluationStage, int] = {
    "context": 1,
    "bundle": 2,
    "accepted": 3,
}


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


def _word_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").split())


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


def _evaluate_bundle(
    root: Path,
    episode_id: str,
    manifest: dict[str, Any],
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
        if _should_check(stage, "bundle"):
            _evaluate_bundle(root, episode_id, manifest, issues)
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
