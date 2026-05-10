import unittest

from consciousness_pipeline.models import Heading, PageText
from consciousness_pipeline.sections import build_sections


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


if __name__ == "__main__":
    unittest.main()
