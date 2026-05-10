import json
from pathlib import Path

from consciousness_pipeline.models import ResearchRecord, Section, SourceRecord

RESEARCH_README = """# Section Research Records

Files in this directory are section-level research records, not podcast episodes.

Each `*.json` file corresponds to one Kuhn taxonomy section from `data/extracted/sections.json`.
Podcast episodes combine one or more of these section records through:

- `course/episode-map.json`
- `episodes/<group-id>/manifest.json`
- `jobs/podcast-scripts.jsonl`

For example, `data/research/1.json` is a reusable research input. It becomes part of a podcast only
when an episode manifest lists it under `research_inputs`.
"""


def empty_research_record(section: Section) -> ResearchRecord:
    return ResearchRecord(
        section_id=section.section_id,
        opening_question=f"What is the strongest case for {section.title}, and where does it fail?",
        core_claim="Research incomplete: use Kuhn's section text as the starting point for this claim.",
        strongest_case="Research incomplete: add the strongest academic case before upload.",
        best_objections="Research incomplete: add at least one serious objection before upload.",
        credibility="Research incomplete",
        listener_hooks=(),
        sources=(SourceRecord(kind="primary", title="A landscape of consciousness", url="", citation="Kuhn 2024"),),
    )


def load_research_record(path: Path, section: Section) -> ResearchRecord:
    if not path.exists():
        return empty_research_record(section)
    data = json.loads(path.read_text(encoding="utf-8"))
    record = ResearchRecord.from_dict(data)
    if record.section_id != section.section_id:
        raise ValueError(
            f"Research record section_id {record.section_id} does not match section {section.section_id}"
        )
    return record


def write_research_stub(path: Path, section: Section) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = empty_research_record(section)
    path.write_text(json.dumps(record.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def write_research_readme(research_dir: Path) -> None:
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "README.md").write_text(RESEARCH_README, encoding="utf-8")
