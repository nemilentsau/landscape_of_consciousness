from typing import Any

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

EPISODE_CAPSULE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "const": "episode_capsule_v1"},
        "episode_id": {"type": "string"},
        "title": {"type": "string"},
        "accepted_dossier_path": {"type": "string"},
        "section_ids": {"type": "array", "items": {"type": "string"}},
        "thesis": {"type": "string"},
        "durable_concepts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "concept": {"type": "string"},
                    "summary": {"type": "string"},
                    "source_path": {"type": "string"},
                },
                "required": ["concept", "summary", "source_path"],
                "additionalProperties": False,
            },
        },
        "recurring_distinctions": {"type": "array", "items": {"type": "string"}},
        "do_not_reexplain": {"type": "array", "items": {"type": "string"}},
        "open_tensions": {"type": "array", "items": {"type": "string"}},
        "callbacks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "concept": {"type": "string"},
                    "family": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                    "source_path": {"type": "string"},
                    "useful_for_future_sections": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["concept", "family", "tags", "summary", "source_path", "useful_for_future_sections"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "schema_version",
        "episode_id",
        "title",
        "accepted_dossier_path",
        "section_ids",
        "thesis",
        "durable_concepts",
        "recurring_distinctions",
        "do_not_reexplain",
        "open_tensions",
        "callbacks",
    ],
    "additionalProperties": False,
}

COURSE_CONTEXT_SELECTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "const": "course_context_selection_v1"},
        "episode_id": {"type": "string"},
        "selected_capsules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "episode_id": {"type": "string"},
                    "selection_type": {"type": "string", "enum": ["recent", "relevant"]},
                    "reason": {"type": "string"},
                },
                "required": ["episode_id", "selection_type", "reason"],
                "additionalProperties": False,
            },
        },
        "selected_callbacks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "concept": {"type": "string"},
                    "episode_id": {"type": "string"},
                    "capsule_path": {"type": "string"},
                    "source_path": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["concept", "episode_id", "capsule_path", "source_path", "reason"],
                "additionalProperties": False,
            },
        },
        "rejected_near_misses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "concept": {"type": "string"},
                    "episode_id": {"type": "string"},
                    "source_path": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["concept", "episode_id", "source_path", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "schema_version",
        "episode_id",
        "selected_capsules",
        "selected_callbacks",
        "rejected_near_misses",
    ],
    "additionalProperties": False,
}

EPISODE_REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "const": "episode_review_v1"},
        "episode_id": {"type": "string"},
        "approved": {"type": "boolean"},
        "summary": {"type": "string"},
        "blocking_issues": {"type": "array", "items": {"type": "string"}},
        "non_blocking_notes": {"type": "array", "items": {"type": "string"}},
        "checked_items": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "schema_version",
        "episode_id",
        "approved",
        "summary",
        "blocking_issues",
        "non_blocking_notes",
        "checked_items",
    ],
    "additionalProperties": False,
}
