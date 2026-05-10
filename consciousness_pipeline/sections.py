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
