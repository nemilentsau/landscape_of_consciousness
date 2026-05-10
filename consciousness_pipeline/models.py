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
