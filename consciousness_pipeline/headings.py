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
