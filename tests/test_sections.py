import unittest

from consciousness_pipeline.core.models import Heading, PageText
from consciousness_pipeline.ingest.sections import build_sections


class SectionSegmentationTest(unittest.TestCase):
    def test_builds_page_ranges_taxonomy_paths_and_section_text(self):
        pages = [
            PageText(page=1, text="1. First theory\nAlpha"),
            PageText(page=2, text="Alpha continued"),
            PageText(page=3, text="1.1. Child theory\nBeta"),
            PageText(page=4, text="2. Second theory\nGamma"),
        ]
        headings = [
            Heading(section_id="1", title="First theory", page=1, level=1, line="1. First theory"),
            Heading(section_id="1.1", title="Child theory", page=3, level=2, line="1.1. Child theory"),
            Heading(section_id="2", title="Second theory", page=4, level=1, line="2. Second theory"),
        ]

        sections = build_sections(pages, headings)
        self.assertEqual(sections[0].start_page, 1)
        self.assertEqual(sections[0].end_page, 2)
        self.assertEqual(list(sections[1].taxonomy_path), ["First theory", "Child theory"])
        self.assertIn("Beta", sections[1].text)
        self.assertEqual(sections[2].slug, "02-second-theory")

    def test_slices_consecutive_same_page_headings(self):
        pages = [
            PageText(
                page=1,
                text="1. Parent\nParent intro\n1.1. First child\nFirst body\n1.2. Second child\nSecond body",
            ),
        ]
        headings = [
            Heading(section_id="1", title="Parent", page=1, level=1, line="1. Parent"),
            Heading(section_id="1.1", title="First child", page=1, level=2, line="1.1. First child"),
            Heading(section_id="1.2", title="Second child", page=1, level=2, line="1.2. Second child"),
        ]

        sections = build_sections(pages, headings)

        self.assertIn("First body", sections[1].text)
        self.assertNotIn("Second body", sections[1].text)
        self.assertIn("Second body", sections[2].text)
        self.assertNotIn("First body", sections[2].text)


if __name__ == "__main__":
    unittest.main()
