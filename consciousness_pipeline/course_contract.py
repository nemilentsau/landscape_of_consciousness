from pathlib import Path

DEFAULT_COURSE_CONTRACT = """# Consciousness Course Contract

## Course Purpose

Build a rigorous listening course on theories of consciousness from Kuhn's taxonomy and serious
external research. Each episode should help a curious but serious listener compare theories without
collapsing unresolved philosophical and scientific disputes into premature answers.

## Production Rules

- Treat each episode dossier as factual source material for NotebookLM, not as a finished dialogue script.
- Keep course continuity explicit, but do not restart the course in every episode.
- Use prior episodes for framing and callbacks only; do not treat prior course summaries as evidence.
- Preserve disagreement where the field is unsettled.

## Epistemic Discipline

- Separate phenomenal consciousness, access consciousness, reportability, wakefulness, and metacognition.
- Separate correlation, causation, constitution, identity, realization, grounding, and explanation.
- Label claims as mainstream scientific theory, active philosophical debate, formal theory, speculative
  extension, religious or spiritual metaphysics, or weakly evidenced claim.
- Distinguish what a theory explains from what it merely redescribes or predicts.

## Recurring Comparison Axes

- What is the target phenomenon?
- What is the proposed ontology?
- What explanatory work does the theory claim to do?
- What evidence or argument supports it?
- What are the strongest objections?
- What nearby theories does it resemble or compete with?
- What should not be overstated?

## NotebookLM Handoff Rules

- NotebookLM generates the conversational audio; this pipeline provides structured research material.
- Do not write host dialogue, speaker labels, stage directions, banter, or finished narration.
- Prefer long, source-rich, clearly sectioned Markdown dossiers for audio generation.
- Keep citations and local source paths traceable.

## Global Do Not Overstate

- Do not imply that neural correlates alone solve the hard problem.
- Do not imply that formal elegance or mathematical vocabulary is empirical confirmation.
- Do not imply that metaphysical breadth is explanatory success.
- Do not imply that a theory's popularity or vividness settles its truth.
"""


def write_default_course_contract(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_COURSE_CONTRACT, encoding="utf-8")
