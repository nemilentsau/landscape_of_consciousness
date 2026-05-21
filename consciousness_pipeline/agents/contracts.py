import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from consciousness_pipeline.contracts.schemas import (
    COURSE_CONTEXT_SELECTION_SCHEMA,
    EPISODE_CAPSULE_SCHEMA,
    EPISODE_REVIEW_SCHEMA,
    RESEARCH_SCHEMA,
    SOURCE_SCRIPT_SCHEMA,
)

AGENT_CHOICES = ("codex", "claude")


@dataclass(frozen=True)
class JobContract:
    kind: str
    manifest_name: str
    schema_name: str
    schema: dict[str, Any]
    prompt_contract: str
    agents: tuple[str, ...]

    @property
    def schema_path(self) -> str:
        return f"schemas/{self.schema_name}"

    def manifest_path(self, root: Path) -> Path:
        return root / "jobs" / self.manifest_name


JOB_CONTRACTS: tuple[JobContract, ...] = (
    JobContract(
        kind="research",
        manifest_name="research.jsonl",
        schema_name="research-record.schema.json",
        schema=RESEARCH_SCHEMA,
        prompt_contract="research_section_v1",
        agents=("codex_exec", "claude_headless"),
    ),
    JobContract(
        kind="source_script",
        manifest_name="source-scripts.jsonl",
        schema_name="source-script.schema.json",
        schema=SOURCE_SCRIPT_SCHEMA,
        prompt_contract="notebooklm_factual_source_script_v2",
        agents=("codex_exec", "claude_headless"),
    ),
    JobContract(
        kind="course_episode_capsule",
        manifest_name="episode-capsules.jsonl",
        schema_name="episode-capsule.schema.json",
        schema=EPISODE_CAPSULE_SCHEMA,
        prompt_contract="course_episode_capsule_v1",
        agents=("codex_exec", "claude_headless"),
    ),
    JobContract(
        kind="course_context_selection",
        manifest_name="course-context-selections.jsonl",
        schema_name="course-context-selection.schema.json",
        schema=COURSE_CONTEXT_SELECTION_SCHEMA,
        prompt_contract="course_context_selection_v1",
        agents=("codex_exec", "claude_headless"),
    ),
    JobContract(
        kind="episode_review",
        manifest_name="episode-reviews.jsonl",
        schema_name="episode-review.schema.json",
        schema=EPISODE_REVIEW_SCHEMA,
        prompt_contract="episode_dossier_review_gate_v1",
        agents=("claude_headless", "codex_exec"),
    ),
)

JOB_CONTRACTS_BY_KIND = {contract.kind: contract for contract in JOB_CONTRACTS}


def job_contract(kind: object) -> JobContract:
    kind_text = str(kind)
    try:
        return JOB_CONTRACTS_BY_KIND[kind_text]
    except KeyError as error:
        raise ValueError(f"Unsupported job kind: {kind_text}") from error


def manifest_path_for_kind(root: Path, kind: object) -> Path:
    return job_contract(kind).manifest_path(root)


def schema_for_kind(kind: object) -> dict[str, Any]:
    return job_contract(kind).schema


def schema_for_job(job: Mapping[str, object]) -> dict[str, Any]:
    return schema_for_kind(job["kind"])


def schema_path_for_kind(kind: object) -> str:
    return job_contract(kind).schema_path


def schema_path_for_job(job: Mapping[str, object]) -> str:
    return schema_path_for_kind(job["kind"])


def write_job_schemas(schemas_dir: Path) -> None:
    schemas_dir.mkdir(parents=True, exist_ok=True)
    for contract in JOB_CONTRACTS:
        path = schemas_dir / contract.schema_name
        path.write_text(
            json.dumps(contract.schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
