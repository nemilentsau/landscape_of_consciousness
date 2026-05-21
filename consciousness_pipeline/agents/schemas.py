from typing import Any

from consciousness_pipeline.course.capsules import EPISODE_CAPSULE_SCHEMA
from consciousness_pipeline.course.context_selection import COURSE_CONTEXT_SELECTION_SCHEMA
from consciousness_pipeline.course.reviews import EPISODE_REVIEW_SCHEMA

__all__ = [
    "COURSE_CONTEXT_SELECTION_SCHEMA",
    "EPISODE_CAPSULE_SCHEMA",
    "EPISODE_REVIEW_SCHEMA",
    "RESEARCH_SCHEMA",
    "SOURCE_SCRIPT_SCHEMA",
]

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
