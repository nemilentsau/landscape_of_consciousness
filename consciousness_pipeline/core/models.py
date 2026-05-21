from collections.abc import Sequence
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
    taxonomy_path: Sequence[str]
    text: str
    slug: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "taxonomy_path", tuple(str(item) for item in self.taxonomy_path))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["taxonomy_path"] = list(self.taxonomy_path)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Section":
        return cls(
            section_id=str(data["section_id"]),
            title=str(data["title"]),
            level=int(data["level"]),
            start_page=int(data["start_page"]),
            end_page=int(data["end_page"]),
            taxonomy_path=tuple(str(item) for item in data["taxonomy_path"]),
            text=str(data["text"]),
            slug=str(data["slug"]),
        )


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
    listener_hooks: Sequence[str]
    sources: Sequence[SourceRecord]

    def __post_init__(self) -> None:
        object.__setattr__(self, "listener_hooks", tuple(str(item) for item in self.listener_hooks))
        object.__setattr__(self, "sources", tuple(self.sources))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["listener_hooks"] = list(self.listener_hooks)
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
            listener_hooks=tuple(str(item) for item in data.get("listener_hooks", [])),
            sources=tuple(SourceRecord.from_dict(item) for item in data.get("sources", [])),
        )
