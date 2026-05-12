from pathlib import Path
from typing import Any

DEFAULT_COURSE_MEMORY = """# Consciousness Course Memory

## Durable Concepts Introduced

- Group 001 established Chalmers's hard problem as the central challenge for phenomenal consciousness.
- Group 001 distinguished phenomenal consciousness, access consciousness, reportability, metacognition,
  wakefulness, and other uses of consciousness.
- Group 001 established epistemology-versus-ontology and correlation-versus-explanation cautions.
- Group 002 introduced the fundamentality fork, identity theory, Kuhn's landscape logic, materialism,
  and non-reductive physicalism.

## Recurring Distinctions

- Phenomenal consciousness versus access consciousness.
- Correlation, causation, constitution, identity, realization, grounding, and explanation.
- Empirical neuroscience, formal theory, active philosophical debate, speculative extension, religious or
  spiritual metaphysics, and weakly evidenced claims.
- Brain dependence versus completed reduction.

## Episode Ledger

- Group 001: hard problem, initial definitions, philosophical tensions, surveys and typologies, opposing worldviews.
- Group 002: consciousness as primitive or fundamental, identity theory, Kuhn's landscape, materialism
  theories, non-reductive physicalism.

## Open Tensions

- The hard problem remains a pressure point rather than a solved premise.
- Brain dependence is strong evidence, but it does not by itself settle identity or reduction.
- Broad taxonomies are useful only if epistemic status is kept visible.

## Do Not Re-Explain

- Do not re-teach Mary's room, zombies, or the hard problem from scratch unless a current section needs
  a short callback.
- Do not redo the general physicalism-versus-nonphysicalism setup.
- Do not treat prior course context as new evidence for current episode claims.

## Next Episode Handoff Notes

- Group 003 should move into theories that challenge, extend, or compete with the physicalist frame:
  quantum theories, IIT, panpsychisms, monisms, and dualisms.
- Keep epistemic-status tagging sharp because group 003 mixes empirical, formal, speculative, and metaphysical theories.
"""


def write_initial_course_memory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_COURSE_MEMORY, encoding="utf-8")


def _section_lines(manifest: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for section in manifest.get("sections", []):
        section_id = str(section["section_id"])
        title = str(section["title"])
        pages = str(section.get("pages", "unknown pages"))
        lines.append(f"- Section {section_id}: {title}. Pages: {pages}.")
    return lines


def render_episode_course_context(manifest: dict[str, Any], course_memory: str) -> str:
    episode_id = str(manifest["episode_id"])
    title = str(manifest["title"])
    question = str(manifest["episode_question"])
    section_lines = "\n".join(_section_lines(manifest))
    return f"""# Course Context For {episode_id}

## Prior Course Grounding

Use the following bounded course memory as continuity guidance. It is not a replacement for current
episode research records or packets.

{course_memory.strip()}

## Already Covered

The course has already introduced the hard problem, phenomenal versus access consciousness,
reportability, epistemology versus ontology, correlation versus explanation, broad worldview framing,
fundamentality, identity theory, materialism, and non-reductive physicalism.

## Current Episode Scope

Episode: {episode_id} - {title}

Episode question: {question}

Current sections:

{section_lines}

## Transition Into This Episode

Group 003 moves into theories that challenge, extend, or compete with the physicalist frame established
in group 002. It should treat quantum theories, integrated information theory, panpsychisms, monisms,
and dualisms as the next major neighborhoods in Kuhn's landscape.

## Production Constraint

Do not re-explain Mary's room, zombies, the hard problem from scratch, or the full materialism setup.
Use those only as short callbacks when needed to explain the current sections.

## Source Priority

The current research records and current packets are factual sources for this episode. The prior course
memory is continuity guidance for framing, pacing, and avoiding repetition.
"""
