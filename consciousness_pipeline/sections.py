import re

from consciousness_pipeline.headings import heading_slug
from consciousness_pipeline.models import Heading, PageText, Section


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _heading_line_index(text: str, heading_line: str) -> int | None:
    normalized_heading = _normalize_line(heading_line)
    for index, line in enumerate(text.splitlines()):
        if _normalize_line(line) == normalized_heading:
            return index
    return None


def _slice_lines(text: str, start_index: int | None = None, end_index: int | None = None) -> str:
    lines = text.splitlines()
    return "\n".join(lines[start_index:end_index]).strip()


def _page_text_for_section(
    pages: list[PageText],
    heading: Heading,
    end_page: int,
    next_heading: Heading | None,
) -> str:
    selected: list[str] = []

    for page in pages:
        if not heading.page <= page.page <= end_page:
            continue

        start_index = None
        end_index = None
        if page.page == heading.page:
            start_index = _heading_line_index(page.text, heading.line)
        if next_heading and next_heading.page == page.page:
            end_index = _heading_line_index(page.text, next_heading.line)

        text = _slice_lines(page.text, start_index, end_index)
        if text:
            selected.append(text)

    return "\n\n".join(selected)


def _taxonomy_path(stack: list[Heading], heading: Heading) -> tuple[str, ...]:
    active = [item for item in stack if item.level < heading.level]
    active.append(heading)
    return tuple(item.title for item in active)


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
                text=_page_text_for_section(pages, heading, end_page, next_heading),
                slug=heading_slug(heading.section_id, heading.title),
            )
        )

    return sections
