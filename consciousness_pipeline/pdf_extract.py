import json
from pathlib import Path
from typing import Callable

from pypdf import PdfReader

from consciousness_pipeline.models import PageText


def extract_pages(pdf_path: Path, reader_factory: Callable[[str], object] = PdfReader) -> list[PageText]:
    reader = reader_factory(str(pdf_path))
    pages: list[PageText] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(PageText(page=index, text=text))
    return pages


def write_pages_json(pages: list[PageText], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([page.to_dict() for page in pages], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
