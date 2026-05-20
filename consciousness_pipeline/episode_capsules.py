import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

EPISODE_CAPSULE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "const": "episode_capsule_v1"},
        "episode_id": {"type": "string"},
        "title": {"type": "string"},
        "accepted_dossier_path": {"type": "string"},
        "section_ids": {"type": "array", "items": {"type": "string"}},
        "thesis": {"type": "string"},
        "durable_concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "concept": {"type": "string"},
                    "summary": {"type": "string"},
                    "source_path": {"type": "string"},
                },
                "required": ["concept", "summary", "source_path"],
                "additionalProperties": False,
            },
        },
        "recurring_distinctions": {"type": "array", "items": {"type": "string"}},
        "do_not_reexplain": {"type": "array", "items": {"type": "string"}},
        "open_tensions": {"type": "array", "items": {"type": "string"}},
        "callbacks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "concept": {"type": "string"},
                    "family": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                    "source_path": {"type": "string"},
                    "useful_for_future_sections": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["concept", "summary", "source_path", "useful_for_future_sections"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "schema_version",
        "episode_id",
        "title",
        "accepted_dossier_path",
        "section_ids",
        "thesis",
        "durable_concepts",
        "recurring_distinctions",
        "do_not_reexplain",
        "open_tensions",
        "callbacks",
    ],
    "additionalProperties": False,
}

REQUIRED_STRING_FIELDS = ("schema_version", "episode_id", "title", "accepted_dossier_path", "thesis")
REQUIRED_LIST_FIELDS = (
    "section_ids",
    "durable_concepts",
    "recurring_distinctions",
    "do_not_reexplain",
    "open_tensions",
    "callbacks",
)
REQUIRED_ENTRY_FIELDS = ("concept", "summary", "source_path")


class EpisodeCapsuleValidationError(ValueError):
    pass


def _resolve_project_path(root: Path, path: object) -> Path:
    candidate = Path(str(path))
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_entries(
    errors: list[str],
    capsule: Mapping[str, Any],
    field: str,
    root: Path | None,
) -> None:
    entries = capsule.get(field)
    if not isinstance(entries, list):
        return
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            errors.append(f"{field}[{index}] must be an object")
            continue
        for entry_field in REQUIRED_ENTRY_FIELDS:
            if not _non_empty_string(entry.get(entry_field)):
                errors.append(f"{field}[{index}].{entry_field} is required")
        if field == "callbacks":
            future_sections = entry.get("useful_for_future_sections")
            if not isinstance(future_sections, list):
                errors.append(f"{field}[{index}].useful_for_future_sections must be a list")
            family = entry.get("family")
            if family is not None and not _non_empty_string(family):
                errors.append(f"{field}[{index}].family must be a non-empty string when provided")
            tags = entry.get("tags")
            if tags is not None:
                if not isinstance(tags, list):
                    errors.append(f"{field}[{index}].tags must be a list when provided")
                else:
                    for tag_index, tag in enumerate(tags):
                        if not _non_empty_string(tag):
                            errors.append(f"{field}[{index}].tags[{tag_index}] must be a non-empty string")
        if root is not None and _non_empty_string(entry.get("source_path")):
            source_path = _resolve_project_path(root, entry["source_path"])
            if not source_path.exists():
                errors.append(f"{field}[{index}].source_path does not exist: {entry['source_path']}")


def validate_episode_capsule(capsule: Mapping[str, Any], root: Path | None = None) -> None:
    errors: list[str] = []
    for field in REQUIRED_STRING_FIELDS:
        if not _non_empty_string(capsule.get(field)):
            errors.append(f"{field} is required")
    for field in REQUIRED_LIST_FIELDS:
        if not isinstance(capsule.get(field), list):
            errors.append(f"{field} must be a list")
    if capsule.get("schema_version") != "episode_capsule_v1":
        errors.append("schema_version must be episode_capsule_v1")
    if isinstance(capsule.get("section_ids"), list) and not capsule["section_ids"]:
        errors.append("section_ids must not be empty")
    if isinstance(capsule.get("durable_concepts"), list) and not capsule["durable_concepts"]:
        errors.append("durable_concepts must not be empty")
    if root is not None and _non_empty_string(capsule.get("accepted_dossier_path")):
        dossier_path = _resolve_project_path(root, capsule["accepted_dossier_path"])
        if not dossier_path.exists():
            errors.append(f"accepted_dossier_path does not exist: {capsule['accepted_dossier_path']}")
    _validate_entries(errors, capsule, "durable_concepts", root)
    _validate_entries(errors, capsule, "callbacks", root)
    if errors:
        raise EpisodeCapsuleValidationError("\n- ".join(errors))


def write_episode_capsule_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(EPISODE_CAPSULE_SCHEMA, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def write_episode_capsule(path: Path, capsule: Mapping[str, Any], root: Path | None = None) -> None:
    validate_episode_capsule(capsule, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(capsule, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
