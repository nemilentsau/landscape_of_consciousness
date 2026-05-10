import csv
import json
from collections import defaultdict
from pathlib import Path

from consciousness_pipeline.config import AUDIO_FORMAT, AUDIO_LANGUAGE, AUDIO_LENGTH, AUDIO_PROMPT
from consciousness_pipeline.models import Section

TOP_LEVEL_GROUP_TITLE = "Top-level sections"


def group_sections(sections: list[Section], max_group_size: int = 5) -> list[dict[str, object]]:
    buckets: dict[str, list[Section]] = defaultdict(list)
    for section in sections:
        key = " -> ".join(section.taxonomy_path[:-1]) if len(section.taxonomy_path) > 1 else TOP_LEVEL_GROUP_TITLE
        buckets[key].append(section)

    groups: list[dict[str, object]] = []
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
        group_lines.append(f"- Script output: `episodes/{group['group_id']}/script.json`")
        group_lines.append(f"- NotebookLM handoff: computer use after script bundle is ready")
        for slug in group["packet_slugs"]:
            group_lines.append(f"- `packets/theories/{slug}.md`")
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
        )
        writer.writeheader()
        for group in groups:
            for section_id, slug in zip(group["section_ids"], group["packet_slugs"]):
                writer.writerow(
                    {
                        "group_id": group["group_id"],
                        "section_id": section_id,
                        "packet_slug": slug,
                        "research_status": "research_queued",
                        "script_status": "script_queued",
                        "notebooklm_status": "not_started",
                        "notebook_url": "",
                        "audio_status": "not_started",
                        "message": "",
                    }
                )
