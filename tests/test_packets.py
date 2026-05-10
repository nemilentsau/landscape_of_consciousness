import unittest

from consciousness_pipeline.models import ResearchRecord, Section, SourceRecord
from consciousness_pipeline.packets import render_packet, validate_packet


class PacketRenderingTest(unittest.TestCase):
    def test_render_packet_contains_notebooklm_audio_guidance_and_sources(self):
        section = Section(
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
        research = ResearchRecord(
            section_id="9.2.3",
            opening_question="Does global broadcast explain consciousness or only reportability?",
            core_claim="Conscious contents become widely available through a global workspace.",
            strongest_case="The theory links reportability, attention, and large-scale neural availability.",
            best_objections="Critics argue global availability may explain access without explaining phenomenal feel.",
            credibility="Mainstream scientific theory",
            listener_hooks=["The theater metaphor makes the dispute vivid."],
            sources=[
                SourceRecord(kind="academic", title="A Cognitive Theory of Consciousness", url="", citation="Baars 1988"),
                SourceRecord(kind="critique", title="Access and phenomenal consciousness", url="", citation="Block 1995"),
            ],
        )

        packet = render_packet(section, research)
        self.assertIn("# Baars's and Dehaene's global workspace theory", packet)
        self.assertIn("Format: Debate", packet)
        self.assertIn("Length: Longer", packet)
        self.assertIn("Does global broadcast explain consciousness", packet)
        self.assertEqual(validate_packet(packet), [])


if __name__ == "__main__":
    unittest.main()
