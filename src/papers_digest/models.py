from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class Paper:
    title: str
    url: str
    published_date: date
    abstract: str | None
    source: str
    authors: tuple[str, ...] = ()


@dataclass(frozen=True)
class DigestItem:
    paper: Paper
    score: float
    highlights: str


@dataclass(frozen=True)
class DigestReport:
    query: str
    run_date: date
    items: tuple[DigestItem, ...]
    recommendations: str

    def top_sources(self) -> set[str]:
        return {item.paper.source for item in self.items}


def unique_by_url(papers: Iterable[Paper]) -> list[Paper]:
    seen: set[str] = set()
    unique: list[Paper] = []
    for paper in papers:
        if paper.url in seen:
            continue
        seen.add(paper.url)
        unique.append(paper)
    return unique
