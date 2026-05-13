import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

COURSE_CONTEXT_SELECTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "const": "course_context_selection_v1"},
        "episode_id": {"type": "string"},
        "selected_capsules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "episode_id": {"type": "string"},
                    "selection_type": {"type": "string", "enum": ["recent", "relevant"]},
                    "reason": {"type": "string"},
                },
                "required": ["episode_id", "selection_type", "reason"],
                "additionalProperties": False,
            },
        },
        "selected_callbacks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "concept": {"type": "string"},
                    "episode_id": {"type": "string"},
                    "capsule_path": {"type": "string"},
                    "source_path": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["concept", "episode_id", "capsule_path", "source_path", "reason"],
                "additionalProperties": False,
            },
        },
        "rejected_near_misses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "concept": {"type": "string"},
                    "episode_id": {"type": "string"},
                    "source_path": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["concept", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "schema_version",
        "episode_id",
        "selected_capsules",
        "selected_callbacks",
        "rejected_near_misses",
    ],
    "additionalProperties": False,
}

REQUIRED_STRING_FIELDS = ("schema_version", "episode_id")
REQUIRED_LIST_FIELDS = ("selected_capsules", "selected_callbacks", "rejected_near_misses")


class CourseContextSelectionValidationError(ValueError):
    pass


def _resolve_project_path(root: Path, path: object) -> Path:
    candidate = Path(str(path))
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _callback_index_matches(
    callback_index: Mapping[str, list[Mapping[str, Any]]],
    selected_callback: Mapping[str, Any],
) -> bool:
    concept = str(selected_callback.get("concept", ""))
    for entry in callback_index.get(concept, []):
        if (
            str(entry.get("episode_id")) == str(selected_callback.get("episode_id"))
            and str(entry.get("capsule_path")) == str(selected_callback.get("capsule_path"))
            and str(entry.get("source_path")) == str(selected_callback.get("source_path"))
        ):
            return True
    return False


def _validate_selected_capsules(errors: list[str], selection: Mapping[str, Any], root: Path | None) -> None:
    capsules = selection.get("selected_capsules")
    if not isinstance(capsules, list):
        return
    for index, capsule in enumerate(capsules):
        if not isinstance(capsule, Mapping):
            errors.append(f"selected_capsules[{index}] must be an object")
            continue
        for field in ("episode_id", "selection_type", "reason"):
            if not _non_empty_string(capsule.get(field)):
                errors.append(f"selected_capsules[{index}].{field} is required")
        if capsule.get("selection_type") not in {"recent", "relevant"}:
            errors.append(f"selected_capsules[{index}].selection_type must be recent or relevant")
        if root is not None and _non_empty_string(capsule.get("episode_id")):
            capsule_path = root / "course" / "episode_capsules" / f"{capsule['episode_id']}.json"
            if not capsule_path.exists():
                errors.append(f"selected_capsules[{index}].episode_id has no capsule: {capsule['episode_id']}")


def _validate_selected_callbacks(errors: list[str], selection: Mapping[str, Any], root: Path | None) -> None:
    callbacks = selection.get("selected_callbacks")
    if not isinstance(callbacks, list):
        return
    callback_index: Mapping[str, list[Mapping[str, Any]]] = {}
    if root is not None:
        callback_index_path = root / "course" / "callback_index.json"
        if callback_index_path.exists():
            callback_index = _read_json(callback_index_path)
    for index, callback in enumerate(callbacks):
        if not isinstance(callback, Mapping):
            errors.append(f"selected_callbacks[{index}] must be an object")
            continue
        for field in ("concept", "episode_id", "capsule_path", "source_path", "reason"):
            if not _non_empty_string(callback.get(field)):
                errors.append(f"selected_callbacks[{index}].{field} is required")
        if root is not None and _non_empty_string(callback.get("source_path")):
            source_path = _resolve_project_path(root, callback["source_path"])
            if not source_path.exists():
                errors.append(f"selected_callbacks[{index}].source_path does not exist: {callback['source_path']}")
        if root is not None and not _callback_index_matches(callback_index, callback):
            errors.append(f"selected_callbacks[{index}] does not match callback_index: {callback.get('concept')}")


def _validate_rejected_near_misses(errors: list[str], selection: Mapping[str, Any]) -> None:
    near_misses = selection.get("rejected_near_misses")
    if not isinstance(near_misses, list):
        return
    for index, near_miss in enumerate(near_misses):
        if not isinstance(near_miss, Mapping):
            errors.append(f"rejected_near_misses[{index}] must be an object")
            continue
        for field in ("concept", "reason"):
            if not _non_empty_string(near_miss.get(field)):
                errors.append(f"rejected_near_misses[{index}].{field} is required")


def validate_course_context_selection(selection: Mapping[str, Any], root: Path | None = None) -> None:
    errors: list[str] = []
    for field in REQUIRED_STRING_FIELDS:
        if not _non_empty_string(selection.get(field)):
            errors.append(f"{field} is required")
    for field in REQUIRED_LIST_FIELDS:
        if not isinstance(selection.get(field), list):
            errors.append(f"{field} must be a list")
    if selection.get("schema_version") != "course_context_selection_v1":
        errors.append("schema_version must be course_context_selection_v1")
    _validate_selected_capsules(errors, selection, root)
    _validate_selected_callbacks(errors, selection, root)
    _validate_rejected_near_misses(errors, selection)
    if errors:
        raise CourseContextSelectionValidationError("\n- ".join(errors))


def write_course_context_selection_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(COURSE_CONTEXT_SELECTION_SCHEMA, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_course_context_selection(path: Path, selection: Mapping[str, Any], root: Path | None = None) -> None:
    validate_course_context_selection(selection, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(selection, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
