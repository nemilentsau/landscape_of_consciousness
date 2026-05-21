import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from consciousness_pipeline.agents.contracts import (
    JOB_CONTRACTS,
    job_contract,
    write_job_schemas,
)
from consciousness_pipeline.core.models import Section
from consciousness_pipeline.course.map import EpisodeGroup, group_sections, write_episode_artifacts


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def _research_job(section: Section) -> dict[str, object]:
    contract = job_contract("research")
    return {
        "job_id": f"research-{section.section_id}",
        "kind": contract.kind,
        "prompt_contract": contract.prompt_contract,
        "agents": list(contract.agents),
        "section_id": section.section_id,
        "title": section.title,
        "taxonomy_path": list(section.taxonomy_path),
        "input_paths": [
            "data/extracted/sections.json",
            f"packets/theories/{section.slug}.md",
        ],
        "output_path": f"data/research/{section.section_id}.json",
    }


def _script_job(group: EpisodeGroup) -> dict[str, object]:
    contract = job_contract("source_script")
    group_id = str(group["group_id"])
    section_ids = [str(item) for item in group["section_ids"]]
    episode_manifest_path = f"episodes/{group_id}/manifest.json"
    course_context_path = f"episodes/{group_id}/course_context.md"
    return {
        "job_id": f"{group_id}-script",
        "kind": contract.kind,
        "prompt_contract": contract.prompt_contract,
        "agents": list(contract.agents),
        "group_id": group_id,
        "title": str(group["title"]),
        "episode_question": str(group["episode_question"]),
        "section_ids": section_ids,
        "packet_slugs": [str(item) for item in group["packet_slugs"]],
        "duration_target": "long_form",
        "tone": "debate_club_balanced",
        "input_paths": [
            "data/extracted/sections.json",
            "course/episode-map.json",
            episode_manifest_path,
            course_context_path,
            *[f"data/research/{section_id}.json" for section_id in section_ids],
        ],
        "episode_manifest_path": episode_manifest_path,
        "course_context_path": course_context_path,
        "output_path": f"episodes/{group_id}/script.json",
        "notebooklm_handoff": "computer_use_after_script_bundle",
        "notebooklm_bundle_dir": f"episodes/{group_id}/notebooklm_bundle",
        "bundle_output_path": f"episodes/{group_id}/notebooklm_bundle/research_dossier.md",
    }


def _episode_capsule_job(group: EpisodeGroup) -> dict[str, object]:
    contract = job_contract("course_episode_capsule")
    group_id = str(group["group_id"])
    episode_manifest_path = f"episodes/{group_id}/manifest.json"
    accepted_dossier_path = f"episodes/{group_id}/notebooklm_bundle/research_dossier.md"
    return {
        "job_id": f"{group_id}-capsule",
        "kind": contract.kind,
        "prompt_contract": contract.prompt_contract,
        "agents": list(contract.agents),
        "group_id": group_id,
        "title": str(group["title"]),
        "section_ids": [str(item) for item in group["section_ids"]],
        "input_paths": [
            "course/course_contract.md",
            episode_manifest_path,
            accepted_dossier_path,
        ],
        "episode_manifest_path": episode_manifest_path,
        "accepted_dossier_path": accepted_dossier_path,
        "output_path": f"course/episode_capsules/{group_id}.json",
    }


def _course_context_selection_job(group: EpisodeGroup) -> dict[str, object]:
    contract = job_contract("course_context_selection")
    group_id = str(group["group_id"])
    episode_manifest_path = f"episodes/{group_id}/manifest.json"
    return {
        "job_id": f"{group_id}-context-selection",
        "kind": contract.kind,
        "prompt_contract": contract.prompt_contract,
        "agents": list(contract.agents),
        "group_id": group_id,
        "title": str(group["title"]),
        "section_ids": [str(item) for item in group["section_ids"]],
        "input_paths": [
            "course/course_contract.md",
            "course/callback_index.json",
            "course/episode_capsules",
            episode_manifest_path,
        ],
        "episode_manifest_path": episode_manifest_path,
        "output_path": f"episodes/{group_id}/context_selection.json",
    }


def _episode_review_job(group: EpisodeGroup) -> dict[str, object]:
    contract = job_contract("episode_review")
    group_id = str(group["group_id"])
    episode_manifest_path = f"episodes/{group_id}/manifest.json"
    source_script_path = f"episodes/{group_id}/script.json"
    dossier_path = f"episodes/{group_id}/notebooklm_bundle/research_dossier.md"
    return {
        "job_id": f"{group_id}-review",
        "kind": contract.kind,
        "prompt_contract": contract.prompt_contract,
        "agents": list(contract.agents),
        "group_id": group_id,
        "title": str(group["title"]),
        "section_ids": [str(item) for item in group["section_ids"]],
        "input_paths": [
            "course/course_contract.md",
            episode_manifest_path,
            source_script_path,
            dossier_path,
        ],
        "episode_manifest_path": episode_manifest_path,
        "source_script_path": source_script_path,
        "dossier_path": dossier_path,
        "output_path": f"episodes/{group_id}/review.json",
    }


def build_research_jobs(sections: list[Section]) -> list[dict[str, object]]:
    return [_research_job(section) for section in sections]


def build_script_jobs(sections: list[Section]) -> list[dict[str, object]]:
    return [_script_job(group) for group in group_sections(sections)]


def build_episode_capsule_jobs(sections: list[Section]) -> list[dict[str, object]]:
    return [_episode_capsule_job(group) for group in group_sections(sections)]


def build_course_context_selection_jobs(sections: list[Section]) -> list[dict[str, object]]:
    return [_course_context_selection_job(group) for group in group_sections(sections)]


def build_episode_review_jobs(sections: list[Section]) -> list[dict[str, object]]:
    return [_episode_review_job(group) for group in group_sections(sections)]


JOB_BUILDERS: dict[str, Callable[[list[Section]], list[dict[str, object]]]] = {
    "research": build_research_jobs,
    "source_script": build_script_jobs,
    "course_episode_capsule": build_episode_capsule_jobs,
    "course_context_selection": build_course_context_selection_jobs,
    "episode_review": build_episode_review_jobs,
}


def write_agent_job_artifacts(
    sections: list[Section],
    jobs_dir: Path,
    schemas_dir: Path,
    episodes_dir: Path,
) -> None:
    jobs_dir.mkdir(parents=True, exist_ok=True)
    schemas_dir.mkdir(parents=True, exist_ok=True)
    episodes_dir.mkdir(parents=True, exist_ok=True)

    write_job_schemas(schemas_dir)
    for contract in JOB_CONTRACTS:
        _write_jsonl(jobs_dir / contract.manifest_name, JOB_BUILDERS[contract.kind](sections))
    write_episode_artifacts(sections, episodes_dir)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def find_job(manifest_path: Path, job_id: str) -> dict[str, Any]:
    for job in load_jsonl(manifest_path):
        if job.get("job_id") == job_id:
            return job
    raise KeyError(f"No job_id {job_id!r} in {manifest_path}")
