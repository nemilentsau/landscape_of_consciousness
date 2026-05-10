# Consciousness Podcast Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible local pipeline that extracts Kuhn's consciousness review, generates exhaustive NotebookLM-ready theory packets, creates course groupings, and dry-runs or executes NotebookLM browser automation with Debate and Longer audio settings.

**Architecture:** Use a small Python package for deterministic local artifacts: PDF extraction, heading detection, section segmentation, packet rendering, validation, and course/status files. Use a separate Node Playwright automation layer for NotebookLM UI work, reading machine-readable course groups and updating the shared production status CSV.

**Tech Stack:** Python 3 stdlib plus `pypdf`; `unittest` for Python tests; Node.js with Playwright for NotebookLM browser automation; Markdown, JSON, and CSV as artifact formats.

---

## File Structure

- Create `consciousness_pipeline/__init__.py`: package marker and version.
- Create `consciousness_pipeline/config.py`: project paths, source filenames, status values, audio settings.
- Create `consciousness_pipeline/models.py`: dataclasses for pages, headings, sections, research records, notebook groups, and production status rows.
- Create `consciousness_pipeline/pdf_extract.py`: PDF to page-aware JSON extraction.
- Create `consciousness_pipeline/headings.py`: numbered heading detection and normalization.
- Create `consciousness_pipeline/sections.py`: section range construction and taxonomy path handling.
- Create `consciousness_pipeline/research.py`: research record loading, validation, and source slot handling.
- Create `consciousness_pipeline/packets.py`: Markdown packet rendering and packet validation.
- Create `consciousness_pipeline/course.py`: exhaustive index, notebook group, machine-readable group JSON, and production status generation.
- Create `consciousness_pipeline/cli.py`: command-line entry point.
- Create `tests/`: stdlib `unittest` coverage for each Python module.
- Create `automation/notebooklm.mjs`: Playwright automation with dry-run and live modes.
- Create `automation/README.md`: NotebookLM automation setup and manual handoff rules.
- Create `package.json`: Node scripts and Playwright dependency.
- Modify `README.md`: project usage, generated artifact map, and first-run commands.

Generated runtime artifacts:

- `data/extracted/paper_pages.json`
- `data/extracted/headings.json`
- `data/extracted/sections.json`
- `data/research/<section-id>.json`
- `packets/theories/<section-id>-<slug>.md`
- `course/exhaustive-index.md`
- `course/notebook-groups.md`
- `course/notebook-groups.json`
- `course/production-status.csv`

## Task 1: Python Package Skeleton And Configuration

**Files:**
- Create: `consciousness_pipeline/__init__.py`
- Create: `consciousness_pipeline/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing configuration test**

Create `tests/test_config.py`:

```python
import unittest
from pathlib import Path

from consciousness_pipeline import __version__
from consciousness_pipeline.config import (
    AUDIO_FORMAT,
    AUDIO_LANGUAGE,
    AUDIO_LENGTH,
    DEFAULT_PDF,
    PROJECT_ROOT,
    STATUS_VALUES,
)


class ConfigTest(unittest.TestCase):
    def test_project_paths_and_audio_defaults(self):
        self.assertEqual(__version__, "0.1.0")
        self.assertEqual(PROJECT_ROOT.name, "landscape_of_consciousness")
        self.assertEqual(DEFAULT_PDF, PROJECT_ROOT / "papers" / "A-landscape-of-consciousness--Toward-a-taxonom_2024_Progress-in-Biophysics-a.pdf")
        self.assertEqual(AUDIO_FORMAT, "Debate")
        self.assertEqual(AUDIO_LENGTH, "Longer")
        self.assertEqual(AUDIO_LANGUAGE, "English")
        self.assertIn("manual_action_required", STATUS_VALUES)
        self.assertIsInstance(PROJECT_ROOT, Path)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_config -v
```

Expected: `ModuleNotFoundError: No module named 'consciousness_pipeline'`.

- [ ] **Step 3: Add minimal package configuration**

Create `consciousness_pipeline/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `consciousness_pipeline/config.py`:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PDF = PROJECT_ROOT / "papers" / "A-landscape-of-consciousness--Toward-a-taxonom_2024_Progress-in-Biophysics-a.pdf"
METADATA_HTML = PROJECT_ROOT / "papers" / "S0079610723001128.html"

EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"
RESEARCH_DIR = PROJECT_ROOT / "data" / "research"
PACKETS_DIR = PROJECT_ROOT / "packets" / "theories"
COURSE_DIR = PROJECT_ROOT / "course"

AUDIO_FORMAT = "Debate"
AUDIO_LENGTH = "Longer"
AUDIO_LANGUAGE = "English"
AUDIO_PROMPT = (
    "Make this a rigorous debate-club style episode. Steelman the theory, "
    "challenge it with serious objections, compare nearby theories, and avoid premature resolution."
)

STATUS_VALUES = (
    "not_started",
    "extracted",
    "researched",
    "packet_ready",
    "upload_attempted",
    "uploaded",
    "audio_requested",
    "audio_ready",
    "failed",
    "manual_action_required",
)
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_config -v
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add consciousness_pipeline/__init__.py consciousness_pipeline/config.py tests/test_config.py
git commit -m "Add pipeline package configuration"
```

## Task 2: Shared Data Models

**Files:**
- Create: `consciousness_pipeline/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing model serialization tests**

Create `tests/test_models.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_models -v
```

Expected: `ModuleNotFoundError: No module named 'consciousness_pipeline.models'`.

- [ ] **Step 3: Add dataclasses with JSON helpers**

Create `consciousness_pipeline/models.py`:

```python
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PageText:
    page: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PageText":
        return cls(page=int(data["page"]), text=str(data["text"]))


@dataclass(frozen=True)
class Heading:
    section_id: str
    title: str
    page: int
    level: int
    line: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Heading":
        return cls(
            section_id=str(data["section_id"]),
            title=str(data["title"]),
            page=int(data["page"]),
            level=int(data["level"]),
            line=str(data["line"]),
        )


@dataclass(frozen=True)
class Section:
    section_id: str
    title: str
    level: int
    start_page: int
    end_page: int
    taxonomy_path: list[str]
    text: str
    slug: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Section":
        return cls(
            section_id=str(data["section_id"]),
            title=str(data["title"]),
            level=int(data["level"]),
            start_page=int(data["start_page"]),
            end_page=int(data["end_page"]),
            taxonomy_path=[str(item) for item in data["taxonomy_path"]],
            text=str(data["text"]),
            slug=str(data["slug"]),
        )
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_models -v
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add consciousness_pipeline/models.py tests/test_models.py
git commit -m "Add pipeline data models"
```

## Task 3: PDF Extraction

**Files:**
- Create: `consciousness_pipeline/pdf_extract.py`
- Create: `tests/test_pdf_extract.py`

- [ ] **Step 1: Write failing extraction tests with a fake reader**

Create `tests/test_pdf_extract.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.pdf_extract import extract_pages, write_pages_json


class FakePage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class FakeReader:
    def __init__(self, path):
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_pdf_extract -v
```

Expected: `ModuleNotFoundError: No module named 'consciousness_pipeline.pdf_extract'`.

- [ ] **Step 3: Implement page extraction and JSON writing**

Create `consciousness_pipeline/pdf_extract.py`:

```python
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
```

- [ ] **Step 4: Run the extraction tests**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_pdf_extract -v
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add consciousness_pipeline/pdf_extract.py tests/test_pdf_extract.py
git commit -m "Add PDF text extraction"
```

## Task 4: Heading Detection

**Files:**
- Create: `consciousness_pipeline/headings.py`
- Create: `tests/test_headings.py`

- [ ] **Step 1: Write failing heading detection tests**

Create `tests/test_headings.py`:

```python
import unittest

from consciousness_pipeline.headings import detect_headings, heading_slug
from consciousness_pipeline.models import PageText


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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_headings -v
```

Expected: `ModuleNotFoundError: No module named 'consciousness_pipeline.headings'`.

- [ ] **Step 3: Implement numbered heading detection**

Create `consciousness_pipeline/headings.py`:

```python
import re

from consciousness_pipeline.models import Heading, PageText

HEADING_RE = re.compile(r"^(?P<section>\d{1,2}(?:\.\d+){0,3})\.\s+(?P<title>\S.*)$")
FALSE_SENTENCE_START_RE = re.compile(r"^(In|There|Therefore|So,)\b")


def _clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _looks_like_heading(title: str) -> bool:
    if not title:
        return False
    if title.endswith("."):
        return False
    if FALSE_SENTENCE_START_RE.match(title):
        return False
    if len(title) > 150:
        return False
    return True


def detect_headings(pages: list[PageText]) -> list[Heading]:
    headings: list[Heading] = []
    seen: set[str] = set()
    for page in pages:
        for raw_line in page.text.splitlines():
            line = _clean_line(raw_line)
            match = HEADING_RE.match(line)
            if not match:
                continue
            section_id = match.group("section")
            title = match.group("title").strip()
            if section_id in seen:
                continue
            if not _looks_like_heading(title):
                continue
            seen.add(section_id)
            headings.append(
                Heading(
                    section_id=section_id,
                    title=title,
                    page=page.page,
                    level=section_id.count(".") + 1,
                    line=line,
                )
            )
    return headings


def heading_slug(section_id: str, title: str) -> str:
    padded = "-".join(part.zfill(2) for part in section_id.split("."))
    normalized = title.lower().replace("'", "")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return f"{padded}-{normalized}"
```

- [ ] **Step 4: Run heading tests**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_headings -v
```

Expected: `OK`.

- [ ] **Step 5: Run a live heading sample against the PDF**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 - <<'PY'
from consciousness_pipeline.config import DEFAULT_PDF
from consciousness_pipeline.pdf_extract import extract_pages
from consciousness_pipeline.headings import detect_headings

pages = extract_pages(DEFAULT_PDF)
headings = detect_headings(pages)
print(len(pages))
print(len(headings))
for heading in headings[:12]:
    print(f"{heading.page}: {heading.section_id} {heading.title}")
PY
```

Expected: first line `142`; heading count greater than `200`; first accepted headings include `1 Chalmers's hard problem of consciousness`, `2 Initial thoughts`, and `9 Materialism theories`.

- [ ] **Step 6: Commit**

```bash
git add consciousness_pipeline/headings.py tests/test_headings.py
git commit -m "Detect numbered theory headings"
```

## Task 5: Section Segmentation

**Files:**
- Create: `consciousness_pipeline/sections.py`
- Create: `tests/test_sections.py`

- [ ] **Step 1: Write failing section segmentation tests**

Create `tests/test_sections.py`:

```python
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
        self.assertEqual(sections[1].taxonomy_path, ["First theory", "Child theory"])
        self.assertIn("Beta", sections[1].text)
        self.assertEqual(sections[2].slug, "02-second-theory")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_sections -v
```

Expected: `ModuleNotFoundError: No module named 'consciousness_pipeline.sections'`.

- [ ] **Step 3: Implement section construction**

Create `consciousness_pipeline/sections.py`:

```python
from consciousness_pipeline.headings import heading_slug
from consciousness_pipeline.models import Heading, PageText, Section


def _page_text_between(pages: list[PageText], start_page: int, end_page: int) -> str:
    selected = [page.text for page in pages if start_page <= page.page <= end_page]
    return "\n\n".join(text.strip() for text in selected if text.strip())


def _taxonomy_path(stack: list[Heading], heading: Heading) -> list[str]:
    active = [item for item in stack if item.level < heading.level]
    active.append(heading)
    return [item.title for item in active]


def build_sections(pages: list[PageText], headings: list[Heading]) -> list[Section]:
    sections: list[Section] = []
    stack: list[Heading] = []
    last_page = pages[-1].page if pages else 0

    for index, heading in enumerate(headings):
        next_heading = headings[index + 1] if index + 1 < len(headings) else None
        end_page = (next_heading.page - 1) if next_heading else last_page
        if end_page < heading.page:
            end_page = heading.page

        stack = [item for item in stack if item.level < heading.level]
        path = _taxonomy_path(stack, heading)
        stack.append(heading)

        sections.append(
            Section(
                section_id=heading.section_id,
                title=heading.title,
                level=heading.level,
                start_page=heading.page,
                end_page=end_page,
                taxonomy_path=path,
                text=_page_text_between(pages, heading.page, end_page),
                slug=heading_slug(heading.section_id, heading.title),
            )
        )

    return sections
```

- [ ] **Step 4: Run section tests**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_sections -v
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add consciousness_pipeline/sections.py tests/test_sections.py
git commit -m "Segment extracted text into sections"
```

## Task 6: Research Records And Packet Rendering

**Files:**
- Extend: `consciousness_pipeline/models.py`
- Create: `consciousness_pipeline/research.py`
- Create: `consciousness_pipeline/packets.py`
- Create: `tests/test_packets.py`

- [ ] **Step 1: Write failing packet rendering tests**

Create `tests/test_packets.py`:

```python
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
            taxonomy_path=["Materialism theories", "Neurobiological theories", "Baars's and Dehaene's global workspace theory"],
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_packets -v
```

Expected: import failure for `ResearchRecord`, `SourceRecord`, or `consciousness_pipeline.packets`.

- [ ] **Step 3: Extend models for research records**

Append to `consciousness_pipeline/models.py`:

```python
@dataclass(frozen=True)
class SourceRecord:
    kind: str
    title: str
    url: str
    citation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceRecord":
        return cls(
            kind=str(data["kind"]),
            title=str(data["title"]),
            url=str(data.get("url", "")),
            citation=str(data["citation"]),
        )


@dataclass(frozen=True)
class ResearchRecord:
    section_id: str
    opening_question: str
    core_claim: str
    strongest_case: str
    best_objections: str
    credibility: str
    listener_hooks: list[str]
    sources: list[SourceRecord]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["sources"] = [source.to_dict() for source in self.sources]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResearchRecord":
        return cls(
            section_id=str(data["section_id"]),
            opening_question=str(data.get("opening_question", "")),
            core_claim=str(data.get("core_claim", "")),
            strongest_case=str(data.get("strongest_case", "")),
            best_objections=str(data.get("best_objections", "")),
            credibility=str(data.get("credibility", "")),
            listener_hooks=[str(item) for item in data.get("listener_hooks", [])],
            sources=[SourceRecord.from_dict(item) for item in data.get("sources", [])],
        )
```

- [ ] **Step 4: Add packet renderer and validator**

Create `consciousness_pipeline/packets.py`:

```python
from consciousness_pipeline.config import AUDIO_FORMAT, AUDIO_LANGUAGE, AUDIO_LENGTH, AUDIO_PROMPT
from consciousness_pipeline.models import ResearchRecord, Section

REQUIRED_MARKERS = (
    "# ",
    "## Course Role",
    "## Kuhn Review Anchor",
    "## Core Claim",
    "## Strongest Case",
    "## Best Objections",
    "## Cross-Examination",
    "## Implications",
    "## Credibility Notes",
    "## Listener Hooks",
    "## Related Packets",
    "## NotebookLM Audio Guidance",
    "## Sources",
    "Format: Debate",
    "Length: Longer",
)


def _bullet_list(items: list[str]) -> str:
    if not items:
        return "- No listener hook recorded yet."
    return "\n".join(f"- {item}" for item in items)


def _sources(research: ResearchRecord) -> str:
    lines = []
    for source in research.sources:
        suffix = f" {source.url}" if source.url else ""
        lines.append(f"- {source.kind}: {source.citation}. {source.title}.{suffix}")
    if not lines:
        lines.append("- Kuhn review anchor only; external research is incomplete.")
    return "\n".join(lines)


def render_packet(section: Section, research: ResearchRecord) -> str:
    taxonomy = " -> ".join(section.taxonomy_path)
    return f"""# {section.title}

## Course Role
This packet supports a debate-club episode on {research.opening_question}

## Kuhn Review Anchor
- Section: {section.section_id}. {section.title}
- Pages: {section.start_page}-{section.end_page}
- Taxonomy placement: {taxonomy}

## Core Claim
{research.core_claim}

## Strongest Case
{research.strongest_case}

## Best Objections
{research.best_objections}

## Cross-Examination
Compare this section with neighboring packets in the taxonomy path: {taxonomy}.

## Implications
- AI consciousness: Not central unless this theory gives explicit criteria for machine consciousness.
- Virtual immortality: Not central unless this theory treats substrate, identity, or mind uploading directly.
- Survival beyond death: Not central unless this theory includes nonphysical survival claims.
- Meaning/value: Not central unless this theory explicitly connects consciousness to value or purpose.

## Credibility Notes
{research.credibility}

## Listener Hooks
{_bullet_list(research.listener_hooks)}

## Related Packets
- Adjacent packets in {taxonomy}

## NotebookLM Audio Guidance
Format: {AUDIO_FORMAT}
Length: {AUDIO_LENGTH}
Language: {AUDIO_LANGUAGE}
Prompt: {AUDIO_PROMPT}

## Sources
- Kuhn review, section {section.section_id}, pages {section.start_page}-{section.end_page}.
{_sources(research)}
"""


def validate_packet(packet: str) -> list[str]:
    missing = [marker for marker in REQUIRED_MARKERS if marker not in packet]
    return [f"Missing marker: {marker}" for marker in missing]
```

- [ ] **Step 5: Add research JSON loader**

Create `consciousness_pipeline/research.py`:

```python
import json
from pathlib import Path

from consciousness_pipeline.models import ResearchRecord, Section, SourceRecord


def empty_research_record(section: Section) -> ResearchRecord:
    return ResearchRecord(
        section_id=section.section_id,
        opening_question=f"What is the strongest case for {section.title}, and where does it fail?",
        core_claim="Research incomplete: use Kuhn's section text as the starting point for this claim.",
        strongest_case="Research incomplete: add the strongest academic case before upload.",
        best_objections="Research incomplete: add at least one serious objection before upload.",
        credibility="Research incomplete",
        listener_hooks=[],
        sources=[SourceRecord(kind="primary", title="A landscape of consciousness", url="", citation="Kuhn 2024")],
    )


def load_research_record(path: Path, section: Section) -> ResearchRecord:
    if not path.exists():
        return empty_research_record(section)
    data = json.loads(path.read_text(encoding="utf-8"))
    return ResearchRecord.from_dict(data)


def write_research_stub(path: Path, section: Section) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = empty_research_record(section)
    path.write_text(json.dumps(record.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
```

- [ ] **Step 6: Run packet tests**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_packets -v
```

Expected: `OK`.

- [ ] **Step 7: Commit**

```bash
git add consciousness_pipeline/models.py consciousness_pipeline/research.py consciousness_pipeline/packets.py tests/test_packets.py
git commit -m "Render NotebookLM-ready theory packets"
```

## Task 7: Course Maps And Production Status

**Files:**
- Extend: `consciousness_pipeline/models.py`
- Create: `consciousness_pipeline/course.py`
- Create: `tests/test_course.py`

- [ ] **Step 1: Write failing course generation tests**

Create `tests/test_course.py`:

```python
import csv
import json
import tempfile
import unittest
from pathlib import Path

from consciousness_pipeline.course import group_sections, write_course_artifacts
from consciousness_pipeline.models import Section


def make_section(section_id, title, parent="Materialism theories"):
    return Section(
        section_id=section_id,
        title=title,
        level=3,
        start_page=20,
        end_page=21,
        taxonomy_path=[parent, "Neurobiological theories", title],
        text=title,
        slug=section_id.replace(".", "-") + "-" + title.lower().replace(" ", "-"),
    )


class CourseGenerationTest(unittest.TestCase):
    def test_group_sections_keeps_groups_small(self):
        sections = [make_section(f"9.2.{index}", f"Theory {index}") for index in range(1, 7)]
        groups = group_sections(sections, max_group_size=5)
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups[0]["packet_slugs"]), 5)
        self.assertEqual(len(groups[1]["packet_slugs"]), 1)

    def test_write_course_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            sections = [make_section("9.2.3", "Global workspace theory")]
            write_course_artifacts(sections, output_dir)

            index = (output_dir / "exhaustive-index.md").read_text(encoding="utf-8")
            groups = json.loads((output_dir / "notebook-groups.json").read_text(encoding="utf-8"))
            rows = list(csv.DictReader((output_dir / "production-status.csv").open(newline="", encoding="utf-8")))

            self.assertIn("Global workspace theory", index)
            self.assertEqual(groups[0]["audio_format"], "Debate")
            self.assertEqual(groups[0]["audio_length"], "Longer")
            self.assertEqual(rows[0]["status"], "packet_ready")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_course -v
```

Expected: `ModuleNotFoundError: No module named 'consciousness_pipeline.course'`.

- [ ] **Step 3: Implement course grouping and status files**

Create `consciousness_pipeline/course.py`:

```python
import csv
import json
from collections import defaultdict
from pathlib import Path

from consciousness_pipeline.config import AUDIO_FORMAT, AUDIO_LANGUAGE, AUDIO_LENGTH, AUDIO_PROMPT
from consciousness_pipeline.models import Section


def group_sections(sections: list[Section], max_group_size: int = 5) -> list[dict[str, object]]:
    buckets: dict[str, list[Section]] = defaultdict(list)
    for section in sections:
        key = " -> ".join(section.taxonomy_path[:-1]) if len(section.taxonomy_path) > 1 else section.title
        buckets[key].append(section)

    groups: list[dict[str, object]] = []
    counter = 1
    for key, bucket in buckets.items():
        for offset in range(0, len(bucket), max_group_size):
            chunk = bucket[offset : offset + max_group_size]
            groups.append(
                {
                    "group_id": f"group-{counter:03d}",
                    "title": key if len(bucket) <= max_group_size else f"{key} Part {(offset // max_group_size) + 1}",
                    "episode_question": f"What is the strongest case for this cluster, and where does it break?",
                    "packet_slugs": [section.slug for section in chunk],
                    "section_ids": [section.section_id for section in chunk],
                    "audio_format": AUDIO_FORMAT,
                    "audio_length": AUDIO_LENGTH,
                    "audio_language": AUDIO_LANGUAGE,
                    "audio_prompt": AUDIO_PROMPT,
                }
            )
            counter += 1
    return groups


def write_course_artifacts(sections: list[Section], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    index_lines = ["# Exhaustive Consciousness Theory Packet Index", ""]
    for section in sections:
        index_lines.append(f"- {section.section_id}. {section.title} — pages {section.start_page}-{section.end_page} — `packets/theories/{section.slug}.md`")
    (output_dir / "exhaustive-index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    groups = group_sections(sections)
    (output_dir / "notebook-groups.json").write_text(json.dumps(groups, indent=2, ensure_ascii=False), encoding="utf-8")

    group_lines = ["# NotebookLM Groups", ""]
    for group in groups:
        group_lines.append(f"## {group['group_id']}: {group['title']}")
        group_lines.append(f"- Episode question: {group['episode_question']}")
        group_lines.append(f"- Audio: {group['audio_format']}, {group['audio_length']}, {group['audio_language']}")
        for slug in group["packet_slugs"]:
            group_lines.append(f"- `packets/theories/{slug}.md`")
        group_lines.append("")
    (output_dir / "notebook-groups.md").write_text("\n".join(group_lines), encoding="utf-8")

    with (output_dir / "production-status.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "group_id",
                "section_id",
                "packet_slug",
                "status",
                "notebook_url",
                "audio_status",
                "message",
            ],
        )
        writer.writeheader()
        for group in groups:
            for section_id, slug in zip(group["section_ids"], group["packet_slugs"]):
                writer.writerow(
                    {
                        "group_id": group["group_id"],
                        "section_id": section_id,
                        "packet_slug": slug,
                        "status": "packet_ready",
                        "notebook_url": "",
                        "audio_status": "not_started",
                        "message": "",
                    }
                )
```

- [ ] **Step 4: Run course tests**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_course -v
```

Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add consciousness_pipeline/course.py tests/test_course.py
git commit -m "Generate course maps and production status"
```

## Task 8: Command-Line Pipeline

**Files:**
- Create: `consciousness_pipeline/cli.py`
- Create: `tests/test_cli.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing CLI smoke tests**

Create `tests/test_cli.py`:

```python
import subprocess
import sys
import unittest


class CliTest(unittest.TestCase):
    def test_help_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "consciousness_pipeline.cli", "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("extract", result.stdout)
        self.assertIn("all", result.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_cli -v
```

Expected: failure because `consciousness_pipeline.cli` does not exist.

- [ ] **Step 3: Implement CLI commands**

Create `consciousness_pipeline/cli.py`:

```python
import argparse
import json
from pathlib import Path

from consciousness_pipeline.config import COURSE_DIR, DEFAULT_PDF, EXTRACTED_DIR, PACKETS_DIR, RESEARCH_DIR
from consciousness_pipeline.course import write_course_artifacts
from consciousness_pipeline.headings import detect_headings
from consciousness_pipeline.models import Heading, PageText, Section
from consciousness_pipeline.packets import render_packet, validate_packet
from consciousness_pipeline.pdf_extract import extract_pages, write_pages_json
from consciousness_pipeline.research import load_research_record, write_research_stub
from consciousness_pipeline.sections import build_sections


def _read_pages(path: Path) -> list[PageText]:
    return [PageText.from_dict(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def _read_headings(path: Path) -> list[Heading]:
    return [Heading.from_dict(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def _read_sections(path: Path) -> list[Section]:
    return [Section.from_dict(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def cmd_extract(args: argparse.Namespace) -> None:
    pages = extract_pages(Path(args.pdf))
    write_pages_json(pages, EXTRACTED_DIR / "paper_pages.json")
    print(f"Extracted {len(pages)} pages")


def cmd_headings(args: argparse.Namespace) -> None:
    pages = _read_pages(EXTRACTED_DIR / "paper_pages.json")
    headings = detect_headings(pages)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    (EXTRACTED_DIR / "headings.json").write_text(json.dumps([item.to_dict() for item in headings], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Detected {len(headings)} headings")


def cmd_sections(args: argparse.Namespace) -> None:
    pages = _read_pages(EXTRACTED_DIR / "paper_pages.json")
    headings = _read_headings(EXTRACTED_DIR / "headings.json")
    sections = build_sections(pages, headings)
    (EXTRACTED_DIR / "sections.json").write_text(json.dumps([item.to_dict() for item in sections], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Built {len(sections)} sections")


def cmd_packets(args: argparse.Namespace) -> None:
    sections = _read_sections(EXTRACTED_DIR / "sections.json")
    PACKETS_DIR.mkdir(parents=True, exist_ok=True)
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for section in sections:
        research_path = RESEARCH_DIR / f"{section.section_id}.json"
        if not research_path.exists():
            write_research_stub(research_path, section)
        research = load_research_record(research_path, section)
        packet = render_packet(section, research)
        errors = validate_packet(packet)
        if errors:
            raise SystemExit(f"Packet validation failed for {section.section_id}: {errors}")
        (PACKETS_DIR / f"{section.slug}.md").write_text(packet, encoding="utf-8")
        written += 1
    print(f"Wrote {written} packets")


def cmd_course(args: argparse.Namespace) -> None:
    sections = _read_sections(EXTRACTED_DIR / "sections.json")
    write_course_artifacts(sections, COURSE_DIR)
    print("Wrote course artifacts")


def cmd_all(args: argparse.Namespace) -> None:
    cmd_extract(args)
    cmd_headings(args)
    cmd_sections(args)
    cmd_packets(args)
    cmd_course(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build consciousness theory packets for NotebookLM")
    parser.add_argument("--pdf", default=str(DEFAULT_PDF), help="Path to the Kuhn review PDF")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, handler in (
        ("extract", cmd_extract),
        ("headings", cmd_headings),
        ("sections", cmd_sections),
        ("packets", cmd_packets),
        ("course", cmd_course),
        ("all", cmd_all),
    ):
        subparser = subparsers.add_parser(name)
        subparser.set_defaults(func=handler)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run CLI tests**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_cli -v
```

Expected: `OK`.

- [ ] **Step 5: Update README with local pipeline commands**

Replace `README.md` with:

````markdown
# landscape_of_consciousness

Pipeline for turning Robert Lawrence Kuhn's "A landscape of consciousness" review into NotebookLM-ready consciousness theory packets and podcast groups.

## Run The Local Pipeline

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m consciousness_pipeline.cli all
```

Generated artifacts:

- `data/extracted/paper_pages.json`
- `data/extracted/headings.json`
- `data/extracted/sections.json`
- `data/research/*.json`
- `packets/theories/*.md`
- `course/exhaustive-index.md`
- `course/notebook-groups.md`
- `course/notebook-groups.json`
- `course/production-status.csv`

## NotebookLM Automation

Run a dry run first:

```bash
npm install
npm run notebooklm:dry-run
```

Live NotebookLM automation is intentionally run only after local packets and course groups have been reviewed.
````

- [ ] **Step 6: Commit**

```bash
git add consciousness_pipeline/cli.py tests/test_cli.py README.md
git commit -m "Add command-line pipeline"
```

## Task 9: NotebookLM Automation Dry Run And Live Harness

**Files:**
- Create: `package.json`
- Create: `automation/notebooklm.mjs`
- Create: `automation/README.md`

- [ ] **Step 1: Create Node package metadata**

Create `package.json`:

```json
{
  "name": "landscape-of-consciousness",
  "private": true,
  "type": "module",
  "scripts": {
    "notebooklm:dry-run": "node automation/notebooklm.mjs --dry-run",
    "notebooklm:live": "node automation/notebooklm.mjs --live"
  },
  "dependencies": {
    "playwright": "^1.44.0"
  }
}
```

- [ ] **Step 2: Write automation script with deterministic dry run**

Create `automation/notebooklm.mjs`:

```javascript
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const groupsPath = path.join(root, "course", "notebook-groups.json");
const packetsDir = path.join(root, "packets", "theories");
const notebookUrl = "https://notebooklm.google.com/";

function parseMode(argv) {
  if (argv.includes("--dry-run")) return "dry-run";
  if (argv.includes("--live")) return "live";
  throw new Error("Use --dry-run or --live");
}

function loadGroups() {
  const raw = fs.readFileSync(groupsPath, "utf8");
  return JSON.parse(raw);
}

function packetPathsFor(group) {
  return group.packet_slugs.map((slug) => path.join(packetsDir, `${slug}.md`));
}

function assertPacketFilesExist(files) {
  const missing = files.filter((file) => !fs.existsSync(file));
  if (missing.length > 0) {
    throw new Error(`Missing packet files:\n${missing.join("\n")}`);
  }
}

async function dryRun(groups) {
  for (const group of groups) {
    const files = packetPathsFor(group);
    assertPacketFilesExist(files);
    console.log(`[dry-run] ${group.group_id}: ${group.title}`);
    console.log(`[dry-run] audio=${group.audio_format}/${group.audio_length}/${group.audio_language}`);
    for (const file of files) console.log(`[dry-run] upload ${file}`);
  }
}

async function liveRun(groups) {
  let chromium;
  try {
    ({ chromium } = await import("playwright"));
  } catch (error) {
    console.error("Playwright is not installed. Run: npm install");
    process.exit(2);
  }

  const userDataDir = path.join(root, ".browser-profiles", "notebooklm");
  const context = await chromium.launchPersistentContext(userDataDir, { headless: false });
  const page = await context.newPage();
  await page.goto(notebookUrl, { waitUntil: "domcontentloaded" });

  console.log("If Google asks for login, complete it in the opened browser window.");
  console.log("Automation will pause for 60 seconds before checking the NotebookLM page.");
  await page.waitForTimeout(60000);

  for (const group of groups) {
    const files = packetPathsFor(group);
    assertPacketFilesExist(files);
    console.log(`[live] ready to create ${group.group_id}: ${group.title}`);
    console.log(`[live] packet files:\n${files.join("\n")}`);
    console.log("[live] Stop here for the first authenticated observation. Record stable UI labels before enabling clicks.");
  }

  await context.close();
}

const mode = parseMode(process.argv.slice(2));
const groups = loadGroups();

if (mode === "dry-run") {
  await dryRun(groups);
} else {
  await liveRun(groups);
}
```

- [ ] **Step 3: Add automation README**

Create `automation/README.md`:

````markdown
# NotebookLM Automation

The automation reads `course/notebook-groups.json`, checks the packet files, and uses a persistent browser profile at `.browser-profiles/notebooklm`.

Run:

```bash
npm install
npm run notebooklm:dry-run
npm run notebooklm:live
```

Manual handoff rules:

- If Google login appears, complete it in the browser window.
- If NotebookLM blocks file upload automation, upload the listed files manually.
- If the Audio Overview controls are visible, choose Debate, Longer, and English.
- Use this prompt:

```text
Make this a rigorous debate-club style episode. Steelman the theory, challenge it with serious objections, compare nearby theories, and avoid premature resolution.
```
````

- [ ] **Step 4: Run dry-run command after local artifacts exist**

Run:

```bash
npm install
npm run notebooklm:dry-run
```

Expected: one `[dry-run]` block per notebook group and one upload line per packet path.

- [ ] **Step 5: Commit**

```bash
git add package.json automation/notebooklm.mjs automation/README.md
git commit -m "Add NotebookLM automation harness"
```

## Task 10: End-To-End Local Smoke Run

**Files:**
- Generated: `data/extracted/paper_pages.json`
- Generated: `data/extracted/headings.json`
- Generated: `data/extracted/sections.json`
- Generated: `data/research/*.json`
- Generated: `packets/theories/*.md`
- Generated: `course/*`

- [ ] **Step 1: Run all Python tests**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Run the local pipeline**

Run:

```bash
PYTHONPATH=. /Users/andreinemilentsau/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m consciousness_pipeline.cli all
```

Expected output includes:

```text
Extracted 142 pages
Detected
Built
Wrote
Wrote course artifacts
```

- [ ] **Step 3: Inspect generated counts**

Run:

```bash
find packets/theories -type f -name '*.md' | wc -l
wc -l course/production-status.csv
```

Expected: packet count greater than `200`; production status rows greater than packet count because of the CSV header.

- [ ] **Step 4: Run NotebookLM dry run**

Run:

```bash
npm run notebooklm:dry-run
```

Expected: dry run prints groups and upload file paths without opening a browser.

- [ ] **Step 5: Commit generated reviewable artifacts**

Commit the generated local artifacts only after inspecting that packet count and headings are plausible:

```bash
git add data/extracted data/research packets course
git commit -m "Generate initial consciousness theory packets"
```

## Task 11: First Live NotebookLM Observation

**Files:**
- Modify: `automation/notebooklm.mjs`
- Modify: `automation/README.md`

- [ ] **Step 1: Run the live harness**

Run:

```bash
npm run notebooklm:live
```

Expected: a visible browser opens at NotebookLM and pauses for Google login. After login, the script prints the first group and packet files.

- [ ] **Step 2: Record observed stable selectors**

Open NotebookLM in the browser window and identify accessible labels for:

```text
Create new notebook
Add source
Upload source
Audio Overview
Customize
Format
Debate
Length
Longer
Generate
```

Write the exact visible labels into `automation/README.md` under a section named `Observed UI Labels`.

- [ ] **Step 3: Add one authenticated flow at a time**

Modify `automation/notebooklm.mjs` by replacing the final informational loop in `liveRun` with one group flow guarded by `--limit=1`. Use Playwright `getByRole` and `getByText` selectors based on the observed labels. Keep these actions in order:

```javascript
await page.getByRole("button", { name: /create/i }).click();
await page.getByRole("textbox").first().fill(group.title);
await page.getByText(/add source/i).click();
const chooserPromise = page.waitForEvent("filechooser");
await page.getByText(/upload/i).click();
const chooser = await chooserPromise;
await chooser.setFiles(files);
await page.getByText(/audio overview/i).click();
await page.getByText(/customize/i).click();
await page.getByText(/debate/i).click();
await page.getByText(/longer/i).click();
await page.getByRole("textbox").last().fill(group.audio_prompt);
await page.getByText(/generate/i).click();
```

- [ ] **Step 4: Run one live group**

Run:

```bash
npm run notebooklm:live -- --limit=1
```

Expected: one notebook is created, packet files upload, Audio Overview is set to Debate and Longer when controls are available, and any blocked step prints an exact manual instruction.

- [ ] **Step 5: Commit automation refinements**

```bash
git add automation/notebooklm.mjs automation/README.md
git commit -m "Refine NotebookLM live automation flow"
```

## Self-Review

Spec coverage:

- PDF extraction is covered by Tasks 3, 8, and 10.
- Heading detection and section segmentation are covered by Tasks 4 and 5.
- NotebookLM-ready packets are covered by Task 6.
- Course maps and production status are covered by Task 7.
- Balanced research support is covered by Task 6 through structured research records and incomplete-source marking.
- Browser automation is covered by Tasks 9 and 11.
- Debate, Longer, and English audio controls are encoded in configuration, packet output, group output, and automation handoff.
- Verification is covered by unittest commands, live PDF smoke checks, dry run, and first live NotebookLM observation.

Plan self-check:

- The plan uses concrete file paths.
- Each code-writing step includes exact file content or exact code to insert.
- Tests precede implementation for Python modules.
- Browser UI automation is split into dry-run harness first, then a one-group authenticated observation before broader live automation.
- No task requires an unofficial NotebookLM API.
