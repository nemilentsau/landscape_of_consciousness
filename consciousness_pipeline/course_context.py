import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from consciousness_pipeline.course_context_selection import validate_course_context_selection
from consciousness_pipeline.course_contract import write_default_course_contract

MAX_RENDERED_DURABLE_CONCEPTS = 3
MAX_RENDERED_DO_NOT_REEXPLAIN = 3
MAX_RENDERED_OPEN_TENSIONS = 5


def _section_lines(manifest: Mapping[str, Any]) -> list[str]:
    lines: list[str] = []
    for section in manifest.get("sections", []):
        section_id = str(section["section_id"])
        title = str(section["title"])
        pages = str(section.get("pages", "unknown pages"))
        lines.append(f"- Section {section_id}: {title}. Pages: {pages}.")
    return lines


def _normalise(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()


def _manifest_search_text(manifest: Mapping[str, Any]) -> str:
    parts = [manifest.get("episode_id", ""), manifest.get("title", ""), manifest.get("episode_question", "")]
    for section in manifest.get("sections", []):
        parts.extend([section.get("section_id", ""), section.get("title", ""), section.get("taxonomy_path", "")])
    return _normalise(" ".join(str(part) for part in parts))


def _callback_matches(concept: str, entry: Mapping[str, Any], search_text: str) -> bool:
    concept_text = _normalise(concept.replace("_", " "))
    if concept_text and concept_text in search_text:
        return True
    for future_section in entry.get("useful_for_future_sections", []):
        future_text = _normalise(future_section)
        if future_text and future_text in search_text:
            return True
    return False


def _selected_callbacks(
    manifest: Mapping[str, Any],
    callback_index: Mapping[str, list[Mapping[str, Any]]],
) -> dict[str, list[Mapping[str, Any]]]:
    search_text = _manifest_search_text(manifest)
    selected: dict[str, list[Mapping[str, Any]]] = {}
    for concept, entries in sorted(callback_index.items()):
        matching_entries = [entry for entry in entries if _callback_matches(concept, entry, search_text)]
        if matching_entries:
            selected[concept] = matching_entries
    return selected


def _unique_lines(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _shorten(value: object, limit: int = 250) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _relevance_score(value: str, search_terms: set[str]) -> int:
    text_terms = set(_normalise(value).split())
    return len(text_terms & search_terms)


def _ranked_unique_lines(values: list[str], search_text: str, limit: int) -> list[str]:
    unique = _unique_lines(values)
    search_terms = {term for term in search_text.split() if len(term) > 2}
    ranked = sorted(
        enumerate(unique),
        key=lambda item: (-_relevance_score(item[1], search_terms), item[0]),
    )
    return [value for _, value in ranked[:limit]]


def _render_capsule_summary(capsule: Mapping[str, Any], selection: Mapping[str, Any] | None = None) -> list[str]:
    lines = [
        f"### {capsule['episode_id']}: {capsule['title']}",
        "",
        f"- Thesis: {_shorten(capsule['thesis'])}",
    ]
    if selection is not None:
        lines.append(f"- Selection: {selection['selection_type']}. {selection['reason']}")
    durable_concepts = capsule.get("durable_concepts", [])
    if durable_concepts:
        concept_names = [str(item["concept"]) for item in durable_concepts[:MAX_RENDERED_DURABLE_CONCEPTS]]
        remaining = len(durable_concepts) - len(concept_names)
        suffix = f"; {remaining} more in capsule" if remaining > 0 else ""
        lines.append(f"- Durable concept handles: {', '.join(concept_names)}{suffix}.")
    lines.append("")
    return lines


def _callback_context(entry: Mapping[str, Any]) -> str:
    details: list[str] = [
        f"episode {entry['episode_id']}",
        f"source `{entry['source_path']}`",
        f"capsule `{entry['capsule_path']}`",
    ]
    if entry.get("family"):
        details.append(f"family `{entry['family']}`")
    tags = entry.get("tags")
    if isinstance(tags, list) and tags:
        details.append("tags " + ", ".join(f"`{tag}`" for tag in tags))
    return "; ".join(details)


def _render_callbacks(callbacks: Mapping[str, list[Mapping[str, Any]]]) -> list[str]:
    if not callbacks:
        return ["- No selected callback-index entries for this episode scope.", ""]
    lines: list[str] = []
    for concept, entries in callbacks.items():
        lines.append(f"### {concept}")
        for entry in entries:
            lines.append(f"- {entry['summary']} ({_callback_context(entry)})")
        lines.append("")
    return lines


def _render_selected_callbacks(callbacks: list[Mapping[str, Any]] | None) -> list[str]:
    if callbacks is None:
        return []
    if not callbacks:
        return ["- No selected callback-index entries for this episode scope.", ""]
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for callback in callbacks:
        grouped.setdefault(str(callback["concept"]), []).append(callback)
    lines: list[str] = []
    for concept, entries in grouped.items():
        lines.append(f"### {concept}")
        for entry in entries:
            summary = str(entry.get("summary") or entry["reason"])
            context = _callback_context(entry)
            lines.append(
                f"- {summary} "
                f"({context}; selection reason: {entry['reason']})"
            )
        lines.append("")
    return lines


def render_episode_course_context(
    manifest: Mapping[str, Any],
    course_contract: str,
    prior_capsules: list[Mapping[str, Any]] | None = None,
    callback_index: Mapping[str, list[Mapping[str, Any]]] | None = None,
    capsule_selection: Mapping[str, Mapping[str, Any]] | None = None,
    selected_callbacks: list[Mapping[str, Any]] | None = None,
) -> str:
    prior_capsules = prior_capsules or []
    callback_index = callback_index or {}
    callbacks = _selected_callbacks(manifest, callback_index) if selected_callbacks is None else {}
    capsule_selection = capsule_selection or {}
    episode_id = str(manifest["episode_id"])
    title = str(manifest["title"])
    question = str(manifest["episode_question"])
    section_lines = "\n".join(_section_lines(manifest))

    prior_lines: list[str] = []
    if prior_capsules:
        for capsule in prior_capsules:
            prior_lines.extend(_render_capsule_summary(capsule, capsule_selection.get(str(capsule["episode_id"]))))
    else:
        prior_lines.extend(["- No accepted prior episode capsules selected.", ""])

    do_not_reexplain = _unique_lines(
        [str(item) for capsule in prior_capsules for item in capsule.get("do_not_reexplain", [])]
    )
    open_tensions = _unique_lines(
        [str(item) for capsule in prior_capsules for item in capsule.get("open_tensions", [])]
    )
    search_text = _manifest_search_text(manifest)
    do_not_reexplain = _ranked_unique_lines(do_not_reexplain, search_text, MAX_RENDERED_DO_NOT_REEXPLAIN)
    open_tensions = _ranked_unique_lines(open_tensions, search_text, MAX_RENDERED_OPEN_TENSIONS)

    do_not_lines = [f"- {item}" for item in do_not_reexplain] or [
        "- No accepted prior do-not-reexplain constraints selected."
    ]
    tension_lines = [f"- {item}" for item in open_tensions] or ["- No accepted prior open tensions selected."]

    return f"""# Course Context For {episode_id}

## Course Contract

{course_contract.strip()}

## Current Episode Scope

Episode: {episode_id} - {title}

Episode question: {question}

Current sections:

{section_lines}

## Selected Prior Grounding

{"\n".join(prior_lines).strip()}

## Relevant Callbacks

{"\n".join(_render_selected_callbacks(selected_callbacks) or _render_callbacks(callbacks)).strip()}

## Do Not Re-Explain

{"\n".join(do_not_lines)}

## Open Tensions To Preserve

{"\n".join(tension_lines)}

## Source Priority

The current research records and packet inputs are factual sources for this episode. The course contract,
selected episode capsules, and callback index are continuity guidance for framing, pacing, and avoiding
repetition. Do not treat prior continuity material as new evidence for current episode claims.
"""


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_prior_capsules(root: Path, episode_id: str, recent_count: int) -> list[Mapping[str, Any]]:
    capsule_dir = root / "course" / "episode_capsules"
    if not capsule_dir.exists():
        return []
    capsule_paths = [
        path for path in sorted(capsule_dir.glob("*.json")) if path.stem < episode_id and path.stem.startswith("group-")
    ]
    return [_read_json(path) for path in capsule_paths[-recent_count:]]


def _load_callback_index(root: Path) -> Mapping[str, list[Mapping[str, Any]]]:
    path = root / "course" / "callback_index.json"
    if not path.exists():
        return {}
    return _read_json(path)


def _selection_callback_details(
    selection: Mapping[str, Any],
    callback_index: Mapping[str, list[Mapping[str, Any]]],
) -> list[Mapping[str, Any]]:
    detailed: list[Mapping[str, Any]] = []
    for selected in selection.get("selected_callbacks", []):
        selected_detail = dict(selected)
        for entry in callback_index.get(str(selected["concept"]), []):
            if (
                str(entry.get("episode_id")) == str(selected["episode_id"])
                and str(entry.get("capsule_path")) == str(selected["capsule_path"])
                and str(entry.get("source_path")) == str(selected["source_path"])
            ):
                selected_detail["summary"] = str(entry["summary"])
                if entry.get("family"):
                    selected_detail["family"] = str(entry["family"])
                if isinstance(entry.get("tags"), list):
                    selected_detail["tags"] = [str(tag) for tag in entry["tags"]]
                break
        detailed.append(selected_detail)
    return detailed


def _load_selection_capsules(
    root: Path,
    selection: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    capsules: list[Mapping[str, Any]] = []
    selection_by_episode: dict[str, Mapping[str, Any]] = {}
    for selected in selection.get("selected_capsules", []):
        episode_id = str(selected["episode_id"])
        capsules.append(_read_json(root / "course" / "episode_capsules" / f"{episode_id}.json"))
        selection_by_episode[episode_id] = selected
    return capsules, selection_by_episode


def write_episode_course_context(
    root: Path,
    episode_id: str,
    recent_count: int = 2,
    selection_path: Path | None = None,
) -> Path:
    contract_path = root / "course" / "course_contract.md"
    if not contract_path.exists():
        write_default_course_contract(contract_path)
    manifest_path = root / "episodes" / episode_id / "manifest.json"
    manifest = _read_json(manifest_path)
    selected_callbacks: list[Mapping[str, Any]] | None = None
    capsule_selection: dict[str, Mapping[str, Any]] | None = None
    if selection_path is None:
        candidate = root / "episodes" / episode_id / "context_selection.json"
        if candidate.exists():
            selection_path = candidate
    if selection_path is not None:
        resolved_selection_path = selection_path if selection_path.is_absolute() else root / selection_path
        selection = _read_json(resolved_selection_path)
        validate_course_context_selection(selection, root=root)
        prior_capsules, capsule_selection = _load_selection_capsules(root, selection)
        selected_callbacks = _selection_callback_details(selection, _load_callback_index(root))
    else:
        prior_capsules = _load_prior_capsules(root, episode_id, recent_count)
    context = render_episode_course_context(
        manifest,
        contract_path.read_text(encoding="utf-8"),
        prior_capsules=prior_capsules,
        callback_index=_load_callback_index(root),
        capsule_selection=capsule_selection,
        selected_callbacks=selected_callbacks,
    )
    output_path = root / "episodes" / episode_id / "course_context.md"
    output_path.write_text(context, encoding="utf-8")
    return output_path
