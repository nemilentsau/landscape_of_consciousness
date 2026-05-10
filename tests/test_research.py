import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.models import ResearchRecord, Section, SourceRecord
from consciousness_pipeline.research import (
    render_notebooklm_research_source,
    write_notebooklm_research_sources,
    write_research_readme,
)


def make_section(section_id: str = "9.2.3", title: str = "Global workspace theory") -> Section:
    return Section(
        section_id=section_id,
        title=title,
        level=3,
        start_page=10,
        end_page=12,
        taxonomy_path=("Materialism", "Neurobiological theories", title),
        text="Section text",
        slug=f"{section_id.replace('.', '-')}-{title.lower().replace(' ', '-')}",
    )


def make_research(section_id: str = "9.2.3") -> ResearchRecord:
    return ResearchRecord(
        section_id=section_id,
        opening_question="What does global broadcast explain?",
        core_claim="Conscious access depends on information being globally available.",
        strongest_case="Workspace models explain report, flexible control, and masking evidence.",
        best_objections="They may explain access without explaining phenomenal character.",
        credibility="Mainstream scientific theory with active debate.",
        listener_hooks=("Debate move: ask whether access is enough.",),
        sources=(
            SourceRecord(
                kind="primary",
                title="A Cognitive Theory of Consciousness",
                url="https://example.test/baars",
                citation="Baars, B. J. (1988). A Cognitive Theory of Consciousness.",
            ),
            SourceRecord(
                kind="listener_hook",
                title="A public-facing article about the theory",
                url="https://example.test/article",
                citation="Example, A. (2024).",
            ),
        ),
    )


class ResearchArtifactsTest(unittest.TestCase):
    def test_write_research_readme_explains_section_episode_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = Path(tmp) / "data" / "research"

            write_research_readme(research_dir)

            readme = (research_dir / "README.md").read_text(encoding="utf-8")
            self.assertIn("section-level", readme)
            self.assertIn("not podcast episodes", readme)
            self.assertIn("episodes/<group-id>/manifest.json", readme)
            self.assertIn("course/episode-map.json", readme)
            self.assertIn("jobs/source-scripts.jsonl", readme)

    def test_render_notebooklm_research_source_is_factual_not_production_guidance(self):
        markdown = render_notebooklm_research_source(make_section(), make_research())

        self.assertIn("# Section 9.2.3: Global workspace theory", markdown)
        self.assertIn("## Core Claim", markdown)
        self.assertIn("Conscious access depends on information being globally available.", markdown)
        self.assertIn("## Sources", markdown)
        self.assertIn("Baars, B. J. (1988). A Cognitive Theory of Consciousness.", markdown)
        self.assertIn("context: Example, A. (2024). A public-facing article", markdown)
        self.assertNotIn("listener_hook", markdown)
        self.assertNotIn("Podcast Production Guidance", markdown)
        self.assertNotIn("Listener Hooks", markdown)
        self.assertNotIn("Debate move", markdown)

    def test_write_notebooklm_research_sources_writes_selected_slugged_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            section = make_section()
            other = make_section("9.2.4", "Multiple drafts")
            research_dir = root / "data" / "research"
            output_dir = root / "episodes" / "group-001" / "notebooklm_bundle" / "sources"
            research_dir.mkdir(parents=True)
            (research_dir / "9.2.3.json").write_text(
                json.dumps(make_research().to_dict()),
                encoding="utf-8",
            )

            written = write_notebooklm_research_sources(
                sections=[section, other],
                section_ids=["9.2.3"],
                research_dir=research_dir,
                output_dir=output_dir,
            )

            self.assertEqual(written, [output_dir / f"{section.slug}.md"])
            self.assertTrue((output_dir / f"{section.slug}.md").exists())
            self.assertFalse((output_dir / f"{other.slug}.md").exists())


if __name__ == "__main__":
    unittest.main()
