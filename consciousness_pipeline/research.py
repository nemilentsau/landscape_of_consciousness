import json
from pathlib import Path

from consciousness_pipeline.models import ResearchRecord, Section, SourceRecord


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
    return ResearchRecord.from_dict(data)


def write_research_stub(path: Path, section: Section) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = empty_research_record(section)
    path.write_text(json.dumps(record.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
