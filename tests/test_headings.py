import unittest

from consciousness_pipeline.core.models import PageText
from consciousness_pipeline.ingest.headings import detect_headings, heading_slug


class HeadingDetectionTest(unittest.TestCase):
    def test_detects_numbered_theory_headings_and_rejects_argument_steps(self):
        pages = [
            PageText(
                page=2,
                text="\n".join(
                    [
                        "1. Chalmers's hard problem of consciousness",
                        "1. In our world, there are conscious experiences.",
                        "2. There is a logically possible world physically identical to ours, in",
                        "3. Therefore, facts about consciousness are further facts about our",
                        "4. So, materialism is false.",
                    ]
                ),
            ),
            PageText(page=4, text="2. Initial thoughts\nBody"),
            PageText(page=13, text="9.1.1. Eliminative materialism/illusionism\nBody"),
        ]

        headings = detect_headings(pages)
        self.assertEqual([heading.section_id for heading in headings], ["1", "2", "9.1.1"])
        self.assertEqual(headings[2].level, 3)
        self.assertEqual(headings[2].title, "Eliminative materialism/illusionism")

    def test_heading_slug_normalizes_section_and_title(self):
        self.assertEqual(
            heading_slug("9.2.3", "Baars's and Dehaene's global workspace theory"),
            "09-02-03-baarss-and-dehaenes-global-workspace-theory",
        )

    def test_heading_slug_normalizes_unicode_apostrophes_like_ascii_apostrophes(self):
        self.assertEqual(
            heading_slug("9.2.3", "Baars’s and Dehaene’s global workspace theory"),
            "09-02-03-baarss-and-dehaenes-global-workspace-theory",
        )

    def test_heading_slug_normalizes_spaced_apostrophes_like_unspaced_apostrophes(self):
        expected = "09-02-03-kochs-consciousness-does-not-depend-on-language"
        self.assertEqual(
            heading_slug("9.2.3", "Koch's consciousness does not depend on language"),
            expected,
        )
        self.assertEqual(
            heading_slug("9.2.3", "Koch’s consciousness does not depend on language"),
            expected,
        )
        self.assertEqual(
            heading_slug("9.2.3", "Koch ’ s consciousness does not depend on language"),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
