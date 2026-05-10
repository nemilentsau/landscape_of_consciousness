from collections.abc import Sequence

from consciousness_pipeline.config import AUDIO_FORMAT, AUDIO_LANGUAGE, AUDIO_LENGTH, AUDIO_PROMPT
from consciousness_pipeline.models import ResearchRecord, Section

REQUIRED_MARKERS = (
    "# ",
    "## Course Role",
    "## Kuhn Review Anchor",
    "## Core Claim",
    "## Strongest Case",
    "## Best Objections",
    "## Cross-Examination",
    "## Implications",
    "## Credibility Notes",
    "## Listener Hooks",
    "## Related Packets",
    "## Podcast Production Guidance",
    "## Sources",
    "NotebookLM format: Deep Dive",
    "Target length: Long-form",
)

REQUIRED_NONEMPTY_SECTIONS = (
    "Course Role",
    "Core Claim",
    "Strongest Case",
    "Best Objections",
    "Credibility Notes",
    "Sources",
)


def _bullet_list(items: Sequence[str]) -> str:
    if not items:
        return "- No listener hook recorded yet."
    return "\n".join(f"- {item}" for item in items)


def _sentence(text: str) -> str:
    return text if text.endswith((".", "?", "!")) else f"{text}."


def _sources(research: ResearchRecord) -> str:
    lines = []
    for source in research.sources:
        suffix = f" {source.url}" if source.url else ""
        lines.append(f"- {source.kind}: {_sentence(source.citation)} {_sentence(source.title)}{suffix}")
    if not lines:
        lines.append("- Kuhn review anchor only; external research is incomplete.")
    return "\n".join(lines)


def render_packet(section: Section, research: ResearchRecord) -> str:
    taxonomy = " -> ".join(section.taxonomy_path)
    return f"""# {section.title}

## Course Role
This packet supports a long-form listening-course episode on {research.opening_question}

## Kuhn Review Anchor
- Section: {section.section_id}. {section.title}
- Pages: {section.start_page}-{section.end_page}
- Taxonomy placement: {taxonomy}

## Core Claim
{research.core_claim}

## Strongest Case
{research.strongest_case}

## Best Objections
{research.best_objections}

## Cross-Examination
Compare this section with neighboring packets in the taxonomy path: {taxonomy}.

## Implications
- AI consciousness: Not central unless this theory gives explicit criteria for machine consciousness.
- Virtual immortality: Not central unless this theory treats substrate, identity, or mind uploading directly.
- Survival beyond death: Not central unless this theory includes nonphysical survival claims.
- Meaning/value: Not central unless this theory explicitly connects consciousness to value or purpose.

## Credibility Notes
{research.credibility}

## Listener Hooks
{_bullet_list(research.listener_hooks)}

## Related Packets
- Adjacent packets in {taxonomy}

## Podcast Production Guidance
NotebookLM format: {AUDIO_FORMAT}
Target length: Long-form
Language: {AUDIO_LANGUAGE}
Custom prompt: {AUDIO_PROMPT}
NotebookLM handoff: use {AUDIO_FORMAT} format and {AUDIO_LENGTH} length after factual source scripts are generated.

## Sources
- Kuhn review, section {section.section_id}, pages {section.start_page}-{section.end_page}.
{_sources(research)}
"""


def _section_body(packet: str, section_name: str) -> str:
    heading = f"## {section_name}"
    start = packet.find(heading)
    if start == -1:
        return ""
    body_start = start + len(heading)
    next_heading = packet.find("\n## ", body_start)
    if next_heading == -1:
        return packet[body_start:]
    return packet[body_start:next_heading]


def validate_packet(packet: str) -> list[str]:
    errors = [f"Missing marker: {marker}" for marker in REQUIRED_MARKERS if marker not in packet]
    for section_name in REQUIRED_NONEMPTY_SECTIONS:
        if f"## {section_name}" in packet and not _section_body(packet, section_name).strip():
            errors.append(f"Empty section: {section_name}")
    return errors
