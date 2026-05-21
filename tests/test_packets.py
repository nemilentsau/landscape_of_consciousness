import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.core.models import ResearchRecord, Section, SourceRecord
from consciousness_pipeline.research.packets import render_packet, validate_packet
from consciousness_pipeline.research.records import load_research_record


class PacketRenderingTest(unittest.TestCase):
    def section(self) -> Section:
        return Section(
            section_id="9.2.3",
            title="Baars's and Dehaene's global workspace theory",
            level=3,
            start_page=21,
            end_page=21,
            taxonomy_path=[
                "Materialism theories",
                "Neurobiological theories",
                "Baars's and Dehaene's global workspace theory",
            ],
            text="9.2.3. Baars's and Dehaene's global workspace theory\nGlobal workspace text.",
            slug="09-02-03-baarss-and-dehaenes-global-workspace-theory",
        )

    def test_render_packet_contains_podcast_production_guidance_and_sources(self):
        section = self.section()
        research = ResearchRecord(
            section_id="9.2.3",
            opening_question="Does global broadcast explain consciousness or only reportability?",
            core_claim="Conscious contents become widely available through a global workspace.",
            strongest_case="The theory links reportability, attention, and large-scale neural availability.",
            best_objections="Critics argue global availability may explain access without explaining phenomenal feel.",
            credibility="Mainstream scientific theory",
            listener_hooks=["The theater metaphor makes the dispute vivid."],
            sources=[
                SourceRecord(
                    kind="academic",
                    title="A Cognitive Theory of Consciousness",
                    url="",
                    citation="Baars 1988.",
                ),
                SourceRecord(
                    kind="critique",
                    title="Access and phenomenal consciousness",
                    url="",
                    citation="Block 1995",
                ),
                SourceRecord(
                    kind="critique",
                    title="Can access explain consciousness?",
                    url="",
                    citation="Question 2024.",
                ),
            ],
        )

        packet = render_packet(section, research)
        self.assertIn("# Baars's and Dehaene's global workspace theory", packet)
        self.assertIn("## Podcast Production Guidance", packet)
        self.assertIn("NotebookLM format: Deep Dive", packet)
        self.assertIn("Target length: Long-form", packet)
        self.assertIn(
            "NotebookLM handoff: use Deep Dive format and Long length after factual source scripts are generated.",
            packet,
        )
        self.assertIn("Steelman physicalist, dualist, idealist, and typological positions", packet)
        self.assertIn("Does global broadcast explain consciousness", packet)
        self.assertNotIn("Baars 1988..", packet)
        self.assertNotIn("consciousness?.", packet)
        self.assertEqual(validate_packet(packet), [])

    def test_validate_packet_rejects_empty_substantive_sections_and_sources(self):
        section = self.section()
        research = ResearchRecord(
            section_id="9.2.3",
            opening_question="Does global broadcast explain consciousness or only reportability?",
            core_claim="",
            strongest_case="",
            best_objections="",
            credibility="",
            listener_hooks=[],
            sources=[],
        )

        packet = render_packet(section, research)
        errors = validate_packet(packet)
        joined_errors = "\n".join(errors)

        self.assertIn("Core Claim", joined_errors)
        self.assertIn("Strongest Case", joined_errors)
        self.assertIn("Best Objections", joined_errors)
        self.assertIn("Credibility Notes", joined_errors)

        empty_sources_packet = packet.replace(
            "- Kuhn review, section 9.2.3, pages 21-21.\n"
            "- Kuhn review anchor only; external research is incomplete.\n",
            "",
        )
        self.assertIn("Sources", "\n".join(validate_packet(empty_sources_packet)))

    def test_load_research_record_rejects_mismatched_section_id(self):
        section = self.section()
        research_data = {
            "section_id": "9.2.4",
            "opening_question": "Question?",
            "core_claim": "Claim.",
            "strongest_case": "Case.",
            "best_objections": "Objections.",
            "credibility": "Credibility.",
            "listener_hooks": [],
            "sources": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "research.json"
            path.write_text(json.dumps(research_data), encoding="utf-8")

            with self.assertRaises(ValueError) as context:
                load_research_record(path, section)

        message = str(context.exception)
        self.assertIn("9.2.3", message)
        self.assertIn("9.2.4", message)


if __name__ == "__main__":
    unittest.main()
