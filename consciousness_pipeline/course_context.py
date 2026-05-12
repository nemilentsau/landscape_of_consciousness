import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from consciousness_pipeline.course_contract import write_default_course_contract


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


def _render_capsule_summary(capsule: Mapping[str, Any]) -> list[str]:
    lines = [
        f"### {capsule['episode_id']}: {capsule['title']}",
        "",
        f"- Thesis: {capsule['thesis']}",
    ]
    durable_concepts = capsule.get("durable_concepts", [])
    if durable_concepts:
        lines.append("- Durable concepts:")
        for item in durable_concepts:
            lines.append(f"  - {item['concept']}: {item['summary']}")
    distinctions = capsule.get("recurring_distinctions", [])
    if distinctions:
        lines.append("- Recurring distinctions:")
        for item in distinctions:
            lines.append(f"  - {item}")
    lines.append("")
    return lines


def _render_callbacks(callbacks: Mapping[str, list[Mapping[str, Any]]]) -> list[str]:
    if not callbacks:
        return ["- No selected callback-index entries for this episode scope.", ""]
    lines: list[str] = []
    for concept, entries in callbacks.items():
        lines.append(f"### {concept}")
        for entry in entries:
            lines.append(
                f"- {entry['summary']} "
                f"(episode {entry['episode_id']}; source `{entry['source_path']}`; capsule `{entry['capsule_path']}`)"
            )
        lines.append("")
    return lines


def render_episode_course_context(
    manifest: Mapping[str, Any],
    course_contract: str,
    prior_capsules: list[Mapping[str, Any]] | None = None,
    callback_index: Mapping[str, list[Mapping[str, Any]]] | None = None,
) -> str:
    prior_capsules = prior_capsules or []
    callback_index = callback_index or {}
    callbacks = _selected_callbacks(manifest, callback_index)
    episode_id = str(manifest["episode_id"])
    title = str(manifest["title"])
    question = str(manifest["episode_question"])
    section_lines = "\n".join(_section_lines(manifest))

    prior_lines: list[str] = []
    if prior_capsules:
        for capsule in prior_capsules:
            prior_lines.extend(_render_capsule_summary(capsule))
    else:
        prior_lines.extend(["- No accepted prior episode capsules selected.", ""])

    do_not_reexplain = _unique_lines(
        [str(item) for capsule in prior_capsules for item in capsule.get("do_not_reexplain", [])]
    )
    open_tensions = _unique_lines(
        [str(item) for capsule in prior_capsules for item in capsule.get("open_tensions", [])]
    )

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

{"\n".join(_render_callbacks(callbacks)).strip()}

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


def write_episode_course_context(root: Path, episode_id: str, recent_count: int = 2) -> Path:
    contract_path = root / "course" / "course_contract.md"
    if not contract_path.exists():
        write_default_course_contract(contract_path)
    manifest_path = root / "episodes" / episode_id / "manifest.json"
    manifest = _read_json(manifest_path)
    context = render_episode_course_context(
        manifest,
        contract_path.read_text(encoding="utf-8"),
        prior_capsules=_load_prior_capsules(root, episode_id, recent_count),
        callback_index=_load_callback_index(root),
    )
    output_path = root / "episodes" / episode_id / "course_context.md"
    output_path.write_text(context, encoding="utf-8")
    return output_path
