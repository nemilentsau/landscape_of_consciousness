import unittest

from consciousness_pipeline.models import Heading, PageText, Section


class ModelsTest(unittest.TestCase):
    def test_page_heading_and_section_roundtrip(self):
        page = PageText(page=12, text="9. Materialism theories\nBody")
        heading = Heading(section_id="9", title="Materialism theories", page=12, level=1, line="9. Materialism theories")
        section = Section(
            section_id="9",
            title="Materialism theories",
            level=1,
            start_page=12,
            end_page=57,
            taxonomy_path=["Materialism theories"],
            text="Body",
            slug="09-materialism-theories",
        )

        self.assertEqual(PageText.from_dict(page.to_dict()), page)
        self.assertEqual(Heading.from_dict(heading.to_dict()), heading)
        self.assertEqual(Section.from_dict(section.to_dict()), section)


if __name__ == "__main__":
    unittest.main()
