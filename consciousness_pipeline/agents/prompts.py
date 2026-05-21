import json
from pathlib import Path
from typing import Any

from consciousness_pipeline.agents.contracts import schema_path_for_job
from consciousness_pipeline.core.models import Section


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
    kind = str(job["kind"])
    if kind == "research":
        sections = _load_sections(root)
        section = sections[str(job["section_id"])]
        return build_research_prompt(job, section)
    if kind == "source_script":
        sections = _load_sections(root)
        group_sections_for_job = [sections[str(section_id)] for section_id in job["section_ids"]]
        return build_script_prompt(job, group_sections_for_job, root)
    if kind == "course_episode_capsule":
        return build_episode_capsule_prompt(job, root)
    if kind == "course_context_selection":
        return build_course_context_selection_prompt(job, root)
    if kind == "episode_review":
        return build_episode_review_prompt(job, root)
    raise ValueError(f"Unsupported job kind: {kind}")


def build_research_prompt(job: dict[str, Any], section: Section) -> str:
    return f"""Research one consciousness-theory section for a listening course.

Job ID: {job["job_id"]}
Output path: {job["output_path"]}
Required schema: {schema_path_for_job(job)}

Kuhn anchor:
{_section_summary(section)}

Use Kuhn's section text as the anchor, then do balanced web research:
- academic core: original papers/books where available, serious reviews, SEP/IEP, university or scholar pages
- critique: serious objections, methodological limits, or competing theories
- listener hooks: debates, thought experiments, vivid examples, or interviews only when useful

Return only JSON matching the schema. Do not write a podcast script in this job.
Label epistemic status plainly: mainstream scientific theory, active philosophical debate,
speculative extension, religious/spiritual metaphysics, or fringe/weakly evidenced claim.
Validation note: the runner performs project validation after this job. Do not import or rely on
`jsonschema`; it is not guaranteed in headless runtimes. If you self-check, use standard JSON parsing
and the required field names in the schema file.

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


def _job_input_text(root: Path, path: object) -> str:
    input_path = Path(str(path))
    resolved_path = input_path if input_path.is_absolute() else root / input_path
    if not resolved_path.exists():
        return f"Missing input: {input_path}"
    return f"Input path: {input_path}\n{_prompt_text(resolved_path.read_text(encoding='utf-8'))}"


def _compact_capsule_metadata(root: Path) -> str:
    capsule_dir = root / "course" / "episode_capsules"
    if not capsule_dir.exists():
        return "[]"
    capsules: list[dict[str, Any]] = []
    for capsule_path in sorted(capsule_dir.glob("*.json")):
        capsule = json.loads(capsule_path.read_text(encoding="utf-8"))
        capsules.append(
            {
                "episode_id": capsule.get("episode_id"),
                "title": capsule.get("title"),
                "accepted_dossier_path": capsule.get("accepted_dossier_path"),
                "section_ids": capsule.get("section_ids", []),
                "thesis": capsule.get("thesis"),
                "durable_concepts": capsule.get("durable_concepts", []),
                "recurring_distinctions": capsule.get("recurring_distinctions", []),
                "do_not_reexplain": capsule.get("do_not_reexplain", []),
                "open_tensions": capsule.get("open_tensions", []),
            }
        )
    return json.dumps(capsules, indent=2, ensure_ascii=False)


def build_course_context_selection_prompt(job: dict[str, Any], root: Path) -> str:
    return f"""Select course continuity context for the next consciousness listening-course episode.

Job ID: {job["job_id"]}
Episode group: {job["group_id"]} - {job["title"]}
Output path: {job["output_path"]}
Required schema: {schema_path_for_job(job)}

Your task is to choose compact continuity guidance for this episode. This is a selection job, not a
research job. Use compact capsule metadata and the callback index; do not read or summarize full prior
dossiers, do not add new course facts, and do not invent callbacks. Every selected callback must already
exist in course/callback_index.json with the same concept, episode_id, capsule_path, and source_path.

Selection rules:
- Select recent capsules only when they help pacing, transitions, do-not-reexplain constraints, or open tensions.
- Select relevant capsules when their compact metadata directly frames the current episode scope.
- Select callbacks for semantic relevance to the current episode, not literal string overlap.
- Prefer a small set of high-value callbacks over broad recall.
- Put plausible but rejected items in rejected_near_misses with concise reasons.
- Reasons must explain why the item helps this exact episode.

Course contract:
{_job_input_text(root, "course/course_contract.md")}

Episode manifest:
{_job_input_text(root, job["episode_manifest_path"])}

Callback index:
{_job_input_text(root, "course/callback_index.json")}

Accepted compact capsule metadata:
{_compact_capsule_metadata(root)}

Return only JSON matching the schema.
Validation note: the runner validates this selection against the schema and callback index. Do not
import or rely on `jsonschema`; if you self-check, use standard JSON parsing and direct callback-index
lookups only.
"""


def build_episode_capsule_prompt(job: dict[str, Any], root: Path) -> str:
    return f"""Create one accepted episode continuity capsule for the consciousness listening course.

Job ID: {job["job_id"]}
Episode group: {job["group_id"]} - {job["title"]}
Output path: {job["output_path"]}
Required schema: {schema_path_for_job(job)}

Your task is to extract durable course continuity from the accepted NotebookLM source dossier:
do not rewrite the whole course, do not add new facts, and do not use this job to repair or expand the
source dossier. Only capture continuity that is explicitly supported by the accepted dossier and
episode manifest.

The capsule must:
- identify only the durable concepts likely to matter in future episodes
- preserve only the sharpest distinctions and open tensions that future episodes should remember
- list only material future episodes should not re-explain from scratch
- add callbacks only when they can point back to the accepted dossier source path
- merge overlapping concepts and callbacks instead of restating every section summary
- prefer fewer, sharper callbacks over comprehensive recap
- include callback family and tags as required advisory grouping hints for future selection
- keep source_path values traceable to the local dossier path

Default memory budget unless this is explicitly a synthesis episode:
- 6-10 durable concepts
- 4-7 recurring distinctions
- 4-7 do-not-reexplain items
- 5-8 open tensions
- 4-7 callbacks

Callback family is required but provisional and free-form, not a strict enum. Callback tags are required,
topic-level strings. Useful seed families include:
target_phenomenon_discipline, bridge_relation_required, epistemic_false_balance,
brain_dependence_constraint, report_not_experience, ai_fluency_not_consciousness,
identity_continuity_required, anomalous_claims_conditional, formalism_not_confirmation,
and metaphysical_breadth_not_explanation.

Course contract:
{_job_input_text(root, "course/course_contract.md")}

Episode manifest:
{_job_input_text(root, job["episode_manifest_path"])}

Accepted dossier:
{_job_input_text(root, job["accepted_dossier_path"])}

Return only JSON matching the schema.
Validation note: the runner validates this capsule and rebuilds the callback index. Do not import or
rely on `jsonschema`; if you self-check, use standard JSON parsing and the schema's required fields.
"""


def build_episode_review_prompt(job: dict[str, Any], root: Path) -> str:
    return f"""Review one generated NotebookLM source dossier as a continuity acceptance gate.

Job ID: {job["job_id"]}
Episode group: {job["group_id"]} - {job["title"]}
Output path: {job["output_path"]}
Required schema: {schema_path_for_job(job)}

This is a review gate. Approve only if the source dossier is suitable to become durable course
continuity for later episodes.

Do not repair the dossier, do not rewrite it, and do not create a replacement. Only review it.

Approve only if:
- the source script JSON and dossier are present and coherent
- missing_inputs is empty
- the dossier is factual NotebookLM source material, not host dialogue, stage directions, banter, or a performed script
- it uses course continuity without treating prior capsules as evidence
- claims are epistemically tagged where the course contract requires it
- major claims are traceable to citations, research inputs, or local source paths
- it does not overstate speculative, spiritual, anomalous, or weakly evidenced claims
- it preserves serious objections and unresolved tensions

Set approved to false if there are blocking issues that would poison future course continuity. Put only
blocking acceptance failures in blocking_issues. Put smaller editorial concerns in non_blocking_notes.

Course contract:
{_job_input_text(root, "course/course_contract.md")}

Episode manifest:
{_job_input_text(root, job["episode_manifest_path"])}

Source script JSON:
{_job_input_text(root, job["source_script_path"])}

NotebookLM dossier:
{_job_input_text(root, job["dossier_path"])}

Return only JSON matching the schema.
Validation note: the runner validates this review output. Do not import or rely on `jsonschema`; if
you self-check, use standard JSON parsing and the schema's required fields.
"""


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
Required schema: {schema_path_for_job(job)}
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
- ## Verdict Matrix
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

Under ## Verdict Matrix, include a compact table that lets NotebookLM compare the covered
positions without drifting into false balance. Use these columns when applicable: Target,
Ontology, Bridge relation, Strongest evidence, Strongest objection, What would change our
mind, and What not to infer. Keep it factual and sourced; mark uncertainty explicitly.

Return only JSON matching the schema. The local runner writes research_dossier_markdown to the
NotebookLM dossier markdown output path for upload.
Validation note: the runner evaluates `--stage dossier` after this job. Do not import or rely on
`jsonschema`; it is not guaranteed in headless runtimes. If you self-check, use
`uv run python -m consciousness_pipeline.cli evaluate-episode --episode-id {job["group_id"]} --stage dossier`
after writing both the JSON output and dossier markdown.
"""
