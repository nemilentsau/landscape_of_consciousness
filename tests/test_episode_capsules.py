import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.episode_capsules import (
    EPISODE_CAPSULE_SCHEMA,
    EpisodeCapsuleValidationError,
    validate_episode_capsule,
    write_episode_capsule,
    write_episode_capsule_schema,
)


def make_capsule() -> dict[str, object]:
    return {
        "schema_version": "episode_capsule_v1",
        "episode_id": "group-002",
        "title": "Top-level sections Part 2",
        "accepted_dossier_path": "episodes/group-002/notebooklm_bundle/research_dossier.md",
        "section_ids": ["6", "7"],
        "thesis": "The episode established the physicalist fork without treating it as settled.",
        "durable_concepts": [
            {
                "concept": "brain_dependence_vs_reduction",
                "summary": "Brain dependence is evidence that still leaves identity and explanation open.",
                "source_path": "episodes/group-002/notebooklm_bundle/research_dossier.md",
            }
        ],
        "recurring_distinctions": ["correlation vs explanation"],
        "do_not_reexplain": ["Do not reteach the hard problem from scratch."],
        "open_tensions": ["Physical dependence and phenomenal explanation remain separable."],
        "callbacks": [
            {
                "concept": "hard_problem",
                "family": "target_phenomenon_discipline",
                "tags": ["hard_problem", "phenomenal_consciousness"],
                "summary": "Use as a pressure point, not a solved premise.",
                "source_path": "episodes/group-002/notebooklm_bundle/research_dossier.md",
                "useful_for_future_sections": ["panpsychism", "integrated information theory"],
            }
        ],
    }


class EpisodeCapsuleTest(unittest.TestCase):
    def test_write_capsule_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "schemas" / "episode-capsule.schema.json"

            write_episode_capsule_schema(path)

            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(schema, EPISODE_CAPSULE_SCHEMA)
            self.assertIn("durable_concepts", schema["required"])
            self.assertIn("accepted_dossier_path", schema["required"])

    def test_validate_capsule_requires_existing_accepted_dossier_and_durable_concepts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capsule = make_capsule()
            dossier = root / str(capsule["accepted_dossier_path"])
            dossier.parent.mkdir(parents=True)
            dossier.write_text("# Accepted dossier\n", encoding="utf-8")

            validate_episode_capsule(capsule, root=root)

            capsule["durable_concepts"] = []
            with self.assertRaises(EpisodeCapsuleValidationError) as context:
                validate_episode_capsule(capsule, root=root)
            self.assertIn("durable_concepts", str(context.exception))

    def test_validate_capsule_accepts_legacy_callbacks_without_family_or_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capsule = make_capsule()
            callbacks = capsule["callbacks"]
            assert isinstance(callbacks, list)
            callback = callbacks[0]
            assert isinstance(callback, dict)
            del callback["family"]
            del callback["tags"]
            dossier = root / str(capsule["accepted_dossier_path"])
            dossier.parent.mkdir(parents=True)
            dossier.write_text("# Accepted dossier\n", encoding="utf-8")

            validate_episode_capsule(capsule, root=root)

    def test_validate_capsule_rejects_missing_source_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capsule = make_capsule()

            with self.assertRaises(EpisodeCapsuleValidationError) as context:
                validate_episode_capsule(capsule, root=root)

            self.assertIn("accepted_dossier_path", str(context.exception))

    def test_write_episode_capsule_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capsule = make_capsule()
            dossier = root / str(capsule["accepted_dossier_path"])
            dossier.parent.mkdir(parents=True)
            dossier.write_text("# Accepted dossier\n", encoding="utf-8")
            path = root / "course" / "episode_capsules" / "group-002.json"

            write_episode_capsule(path, capsule, root=root)

            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.endswith("\n"))
            self.assertEqual(json.loads(text), capsule)
            self.assertLess(text.index('"accepted_dossier_path"'), text.index('"callbacks"'))


if __name__ == "__main__":
    unittest.main()
