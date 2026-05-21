import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.ingest.pdf_extract import extract_pages, write_pages_json


class FakePage:
    def __init__(self, text: str | None):
        self._text = text

    def extract_text(self) -> str | None:
        return self._text


class FakeReader:
    def __init__(self, path: str):
        self.path = path
        self.pages = [FakePage("first page"), FakePage(None), FakePage("third page")]


class PdfExtractTest(unittest.TestCase):
    def test_extract_pages_preserves_page_numbers_and_empty_text(self):
        pages = extract_pages(Path("paper.pdf"), reader_factory=FakeReader)
        self.assertEqual([page.page for page in pages], [1, 2, 3])
        self.assertEqual([page.text for page in pages], ["first page", "", "third page"])

    def test_write_pages_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "paper_pages.json"
            pages = extract_pages(Path("paper.pdf"), reader_factory=FakeReader)
            write_pages_json(pages, output)
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data[0]["page"], 1)
            self.assertEqual(data[2]["text"], "third page")


if __name__ == "__main__":
    unittest.main()
