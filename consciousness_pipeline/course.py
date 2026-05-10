import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import TypedDict

from consciousness_pipeline.config import AUDIO_FORMAT, AUDIO_LANGUAGE, AUDIO_LENGTH, AUDIO_PROMPT
from consciousness_pipeline.models import Section

TOP_LEVEL_GROUP_TITLE = "Top-level sections"


class AudioProfile(TypedDict):
    format: str
    length: str
    language: str
    prompt: str


class EpisodeGroup(TypedDict):
    group_id: str
    title: str
    episode_question: str
    packet_slugs: list[str]
    section_ids: list[str]
    audio_profile: AudioProfile


class EpisodeManifestSection(TypedDict):
    section_id: str
    title: str
    pages: str
    taxonomy_path: list[str]
    research_path: str
    packet_path: str


class EpisodeManifest(TypedDict):
    episode_id: str
    title: str
    episode_question: str
    section_count: int
    section_ids: list[str]
    sections: list[EpisodeManifestSection]
    research_inputs: list[str]
    packet_inputs: list[str]
    script_job_id: str
    script_job_manifest: str
    script_output: str
    bundle_output_path: str
    notebooklm_bundle_dir: str
    notebooklm_handoff: str
    audio_profile: AudioProfile


def group_sections(sections: list[Section], max_group_size: int = 5) -> list[EpisodeGroup]:
    buckets: dict[str, list[Section]] = defaultdict(list)
    for section in sections:
        key = " -> ".join(section.taxonomy_path[:-1]) if len(section.taxonomy_path) > 1 else TOP_LEVEL_GROUP_TITLE
        buckets[key].append(section)

    groups: list[EpisodeGroup] = []
    counter = 1
    for key, bucket in buckets.items():
        for offset in range(0, len(bucket), max_group_size):
            chunk = bucket[offset : offset + max_group_size]
            groups.append(
                {
                    "group_id": f"group-{counter:03d}",
                    "title": key if len(bucket) <= max_group_size else f"{key} Part {(offset // max_group_size) + 1}",
                    "episode_question": "What is the strongest case for this cluster, and where does it break?",
                    "packet_slugs": [section.slug for section in chunk],
                    "section_ids": [section.section_id for section in chunk],
                    "audio_profile": {
                        "format": AUDIO_FORMAT,
                        "length": AUDIO_LENGTH,
                        "language": AUDIO_LANGUAGE,
                        "prompt": AUDIO_PROMPT,
                    },
                }
            )
            counter += 1
    return groups


def build_episode_manifests(sections: list[Section]) -> list[EpisodeManifest]:
    section_lookup = {section.section_id: section for section in sections}
    manifests: list[EpisodeManifest] = []
    for group in group_sections(sections):
        group_id = group["group_id"]
        manifest_sections: list[EpisodeManifestSection] = []
        for section_id, packet_slug in zip(group["section_ids"], group["packet_slugs"], strict=True):
            section = section_lookup[section_id]
            manifest_sections.append(
                {
                    "section_id": section.section_id,
                    "title": section.title,
                    "pages": f"{section.start_page}-{section.end_page}",
                    "taxonomy_path": list(section.taxonomy_path),
                    "research_path": f"data/research/{section.section_id}.json",
                    "packet_path": f"packets/theories/{packet_slug}.md",
                }
            )
        research_inputs = [section["research_path"] for section in manifest_sections]
        packet_inputs = [section["packet_path"] for section in manifest_sections]
        manifests.append(
            {
                "episode_id": group_id,
                "title": group["title"],
                "episode_question": group["episode_question"],
                "section_count": len(manifest_sections),
                "section_ids": list(group["section_ids"]),
                "sections": manifest_sections,
                "research_inputs": research_inputs,
                "packet_inputs": packet_inputs,
                "script_job_id": f"{group_id}-script",
                "script_job_manifest": "jobs/source-scripts.jsonl",
                "script_output": f"episodes/{group_id}/script.json",
                "bundle_output_path": f"episodes/{group_id}/notebooklm_bundle/research_dossier.md",
                "notebooklm_bundle_dir": f"episodes/{group_id}/notebooklm_bundle",
                "notebooklm_handoff": "computer_use_after_script_bundle",
                "audio_profile": group["audio_profile"],
            }
        )
    return manifests


def render_episode_readme(manifest: EpisodeManifest) -> str:
    lines = [
        f"# {manifest['episode_id']}: {manifest['title']}",
        "",
        "This is one podcast episode group. It combines section-level research records "
        "into one factual NotebookLM source script.",
        "",
        f"- Episode question: {manifest['episode_question']}",
        f"- Script job: `{manifest['script_job_id']}` in `{manifest['script_job_manifest']}`",
        f"- Script JSON output: `{manifest['script_output']}`",
        f"- NotebookLM dossier output: `{manifest['bundle_output_path']}`",
        f"- NotebookLM bundle: `{manifest['notebooklm_bundle_dir']}`",
        "",
        "## Section Inputs",
        "",
        "| Section | Title | Research record | Packet |",
        "| --- | --- | --- | --- |",
    ]
    for section in manifest["sections"]:
        lines.append(
            f"| {section['section_id']} | {section['title']} | `{section['research_path']}` | "
            f"`{section['packet_path']}` |"
        )
    lines.extend(
        [
            "",
            "Research records are reusable section inputs, not podcast episodes. This directory shows how those",
            "section records are assembled into this one episode.",
            "",
        ]
    )
    return "\n".join(lines)


def write_episode_artifacts(sections: list[Section], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for manifest in build_episode_manifests(sections):
        episode_dir = output_dir / manifest["episode_id"]
        episode_dir.mkdir(parents=True, exist_ok=True)
        (episode_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (episode_dir / "README.md").write_text(render_episode_readme(manifest), encoding="utf-8")


def write_course_artifacts(sections: list[Section], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    index_lines = ["# Exhaustive Consciousness Theory Packet Index", ""]
    for section in sections:
        index_lines.append(
            f"- {section.section_id}. {section.title} - pages {section.start_page}-{section.end_page} - "
            f"`packets/theories/{section.slug}.md`"
        )
    (output_dir / "exhaustive-index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    groups = group_sections(sections)
    (output_dir / "episode-map.json").write_text(json.dumps(groups, indent=2, ensure_ascii=False), encoding="utf-8")

    group_lines = ["# Podcast Episode Map", ""]
    for group in groups:
        group_lines.append(f"## {group['group_id']}: {group['title']}")
        group_lines.append(f"- Episode question: {group['episode_question']}")
        audio_profile = group["audio_profile"]
        group_lines.append(
            f"- Audio target: {audio_profile['format']}, {audio_profile['length']}, {audio_profile['language']}"
        )
        group_lines.append(f"- Episode manifest: `episodes/{group['group_id']}/manifest.json`")
        group_lines.append(f"- Factual source script: `episodes/{group['group_id']}/script.json`")
        group_lines.append(
            f"- NotebookLM dossier: `episodes/{group['group_id']}/notebooklm_bundle/research_dossier.md`"
        )
        group_lines.append("- NotebookLM handoff: computer use after script bundle is ready")
        group_lines.append("- Section inputs:")
        for section_id, slug in zip(group["section_ids"], group["packet_slugs"], strict=True):
            group_lines.append(f"  - `{section_id}`: `data/research/{section_id}.json` + `packets/theories/{slug}.md`")
        group_lines.append("")
    (output_dir / "episode-map.md").write_text("\n".join(group_lines), encoding="utf-8")

    with (output_dir / "production-status.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "group_id",
                "section_id",
                "packet_slug",
                "research_status",
                "script_status",
                "notebooklm_status",
                "notebook_url",
                "audio_status",
                "message",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for group in groups:
            for section_id, slug in zip(group["section_ids"], group["packet_slugs"], strict=True):
                writer.writerow(
                    {
                        "group_id": group["group_id"],
                        "section_id": section_id,
                        "packet_slug": slug,
                        "research_status": "research_queued",
                        "script_status": "source_script_queued",
                        "notebooklm_status": "not_started",
                        "notebook_url": "",
                        "audio_status": "not_started",
                        "message": "",
                    }
                )
