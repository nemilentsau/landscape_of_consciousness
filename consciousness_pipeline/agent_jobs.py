import json
from pathlib import Path
from typing import Any

from consciousness_pipeline.course import EpisodeGroup, group_sections, write_episode_artifacts
from consciousness_pipeline.models import Section

RESEARCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "section_id": {"type": "string"},
        "opening_question": {"type": "string"},
        "core_claim": {"type": "string"},
        "strongest_case": {"type": "string"},
        "best_objections": {"type": "string"},
        "credibility": {"type": "string"},
        "listener_hooks": {"type": "array", "items": {"type": "string"}},
        "sources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string"},
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "citation": {"type": "string"},
                },
                "required": ["kind", "title", "url", "citation"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "section_id",
        "opening_question",
        "core_claim",
        "strongest_case",
        "best_objections",
        "credibility",
        "listener_hooks",
        "sources",
    ],
    "additionalProperties": False,
}

SOURCE_SCRIPT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "episode_id": {"type": "string"},
        "title": {"type": "string"},
        "episode_question": {"type": "string"},
        "duration_target": {"type": "string"},
        "research_dossier_markdown": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
        "missing_inputs": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "episode_id",
        "title",
        "episode_question",
        "duration_target",
        "research_dossier_markdown",
        "citations",
        "missing_inputs",
    ],
    "additionalProperties": False,
}


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def _research_job(section: Section) -> dict[str, object]:
    return {
        "job_id": f"research-{section.section_id}",
        "kind": "research",
        "prompt_contract": "research_section_v1",
        "agents": ["codex_exec", "claude_headless"],
        "section_id": section.section_id,
        "title": section.title,
        "taxonomy_path": list(section.taxonomy_path),
        "input_paths": [
            "data/extracted/sections.json",
            f"packets/theories/{section.slug}.md",
        ],
        "output_path": f"data/research/{section.section_id}.json",
        "schema_path": "schemas/research-record.schema.json",
    }


def _script_job(group: EpisodeGroup) -> dict[str, object]:
    group_id = str(group["group_id"])
    section_ids = [str(item) for item in group["section_ids"]]
    episode_manifest_path = f"episodes/{group_id}/manifest.json"
    return {
        "job_id": f"{group_id}-script",
        "kind": "source_script",
        "prompt_contract": "notebooklm_factual_source_script_v1",
        "agents": ["codex_exec", "claude_headless"],
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
            *[f"data/research/{section_id}.json" for section_id in section_ids],
        ],
        "episode_manifest_path": episode_manifest_path,
        "output_path": f"episodes/{group_id}/script.json",
        "schema_path": "schemas/source-script.schema.json",
        "notebooklm_handoff": "computer_use_after_script_bundle",
        "notebooklm_bundle_dir": f"episodes/{group_id}/notebooklm_bundle",
        "bundle_output_path": f"episodes/{group_id}/notebooklm_bundle/research_dossier.md",
    }


def build_research_jobs(sections: list[Section]) -> list[dict[str, object]]:
    return [_research_job(section) for section in sections]


def build_script_jobs(sections: list[Section]) -> list[dict[str, object]]:
    return [_script_job(group) for group in group_sections(sections)]


def write_agent_job_artifacts(
    sections: list[Section],
    jobs_dir: Path,
    schemas_dir: Path,
    episodes_dir: Path,
) -> None:
    jobs_dir.mkdir(parents=True, exist_ok=True)
    schemas_dir.mkdir(parents=True, exist_ok=True)
    episodes_dir.mkdir(parents=True, exist_ok=True)

    for legacy_path in (jobs_dir / "podcast-scripts.jsonl", schemas_dir / "podcast-script.schema.json"):
        if legacy_path.exists():
            legacy_path.unlink()

    _write_json(schemas_dir / "research-record.schema.json", RESEARCH_SCHEMA)
    _write_json(schemas_dir / "source-script.schema.json", SOURCE_SCRIPT_SCHEMA)
    _write_jsonl(jobs_dir / "research.jsonl", build_research_jobs(sections))
    _write_jsonl(jobs_dir / "source-scripts.jsonl", build_script_jobs(sections))
    write_episode_artifacts(sections, episodes_dir)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def find_job(manifest_path: Path, job_id: str) -> dict[str, Any]:
    for job in load_jsonl(manifest_path):
        if job.get("job_id") == job_id:
            return job
    raise KeyError(f"No job_id {job_id!r} in {manifest_path}")


def _section_summary(section: Section) -> str:
    taxonomy = _prompt_text(" -> ".join(section.taxonomy_path))
    return (
        f"- {section.section_id}. {_prompt_text(section.title)}\n"
        f"  Pages: {section.start_page}-{section.end_page}\n"
        f"  Taxonomy: {taxonomy}\n"
        f"  Packet: packets/theories/{section.slug}.md"
    )


def _prompt_text(text: str) -> str:
    return text.replace("\x00", "")


def _load_sections(root: Path) -> dict[str, Section]:
    sections_path = root / "data" / "extracted" / "sections.json"
    sections = [Section.from_dict(item) for item in json.loads(sections_path.read_text(encoding="utf-8"))]
    return {section.section_id: section for section in sections}


def build_job_prompt(job: dict[str, Any], root: Path) -> str:
    sections = _load_sections(root)
    kind = str(job["kind"])
    if kind == "research":
        section = sections[str(job["section_id"])]
        return build_research_prompt(job, section)
    if kind == "source_script":
        group_sections_for_job = [sections[str(section_id)] for section_id in job["section_ids"]]
        return build_script_prompt(job, group_sections_for_job, root)
    raise ValueError(f"Unsupported job kind: {kind}")


def build_research_prompt(job: dict[str, Any], section: Section) -> str:
    return f"""Research one consciousness-theory section for a listening course.

Job ID: {job["job_id"]}
Output path: {job["output_path"]}
Required schema: {job["schema_path"]}

Kuhn anchor:
{_section_summary(section)}

Use Kuhn's section text as the anchor, then do balanced web research:
- academic core: original papers/books where available, serious reviews, SEP/IEP, university or scholar pages
- critique: serious objections, methodological limits, or competing theories
- listener hooks: debates, thought experiments, vivid examples, or interviews only when useful

Return only JSON matching the schema. Do not write a podcast script in this job.
Label epistemic status plainly: mainstream scientific theory, active philosophical debate,
speculative extension, religious/spiritual metaphysics, or fringe/weakly evidenced claim.

Section text:
{_prompt_text(section.text)}
"""


def _course_context_block(job: dict[str, Any], root: Path) -> str:
    context_path = Path(str(job.get("course_context_path", f"episodes/{job['group_id']}/course_context.md")))
    resolved_context_path = context_path if context_path.is_absolute() else root / context_path
    if not resolved_context_path.exists():
        return "Course context: none provided."
    context_text = _prompt_text(resolved_context_path.read_text(encoding="utf-8"))
    return (
        f"Course context path: {context_path}\n"
        "Use this context to continue the course instead of restarting already-covered material.\n\n"
        f"{context_text}"
    )


def build_script_prompt(job: dict[str, Any], sections: list[Section], root: Path) -> str:
    summaries = "\n".join(_section_summary(section) for section in sections)
    research_paths = "\n".join(f"- data/research/{section.section_id}.json" for section in sections)
    course_context = _course_context_block(job, root)
    return f"""Write one factual NotebookLM source dossier for the consciousness listening course.

Job ID: {job["job_id"]}
Episode group: {job["group_id"]} - {job["title"]}
Episode question: {job["episode_question"]}
Episode manifest: {job["episode_manifest_path"]}
Output path: {job["output_path"]}
Required schema: {job["schema_path"]}
NotebookLM handoff: {job["notebooklm_handoff"]}; bundle dir {job["notebooklm_bundle_dir"]}
NotebookLM dossier markdown output: {job["bundle_output_path"]}

Sections:
{summaries}

Research inputs to read:
{research_paths}

Course continuity context:
{course_context}

Produce thorough research material for NotebookLM to work with. NotebookLM will generate the conversational audio.
Do not write dialogue, speaker names, stage directions, banter, cold opens, finished narration, or host patter.

The research_dossier_markdown should be factual and structured. Use these top-level Markdown
sections in this order:
- ## Episode Metadata
- ## Course Continuity Grounding
- ## Episode Scope And Why These Sections Are Grouped
- ## Concise Thesis Of The Cluster
- ## Per-Section Factual Summaries
- ## Strongest Academic Case For The Cluster
- ## Serious Objections And Limits
- ## Comparison Axes For Theories In This Cluster
- ## Epistemic Status And What Not To Overstate
- ## Implications Only Where Sources Justify Them
- ## Source Notes And Local Input Paths

Under ## Course Continuity Grounding, summarize what prior episode context already covered,
state what this episode should not re-explain, and identify the transition into the current
episode. Do not bury course continuity inside the episode-scope section.

Return only JSON matching the schema. The local runner writes research_dossier_markdown to the
NotebookLM dossier markdown output path for upload.
"""
