from __future__ import annotations

from datetime import date
from typing import Iterable

import requests

from papers_digest.models import Paper
from papers_digest.sources.base import PaperSource


class OpenAlexSource(PaperSource):
    name = "openalex"

    def fetch(self, target_date: date, query: str) -> Iterable[Paper]:
        target = target_date.strftime("%Y-%m-%d")
        url = "https://api.openalex.org/works"
        params = {
            "filter": f"from_publication_date:{target},to_publication_date:{target}",
            "search": query.strip() or "artificial intelligence",
            "per-page": 50,
        }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        items = response.json().get("results", [])

        for item in items:
            title = item.get("title", "")
            abstract = _abstract_from_openalex(item)
            authors = [
                author.get("author", {}).get("display_name", "")
                for author in item.get("authorships", [])
                if author.get("author")
            ]
            if not title:
                continue
            yield Paper(
                paper_id=item.get("id", ""),
                title=title,
                abstract=abstract,
                authors=authors,
                url=item.get("id", ""),
                published_date=target_date,
                source=self.name,
            )


def _abstract_from_openalex(item: dict) -> str:
    abstract = item.get("abstract", "")
    if abstract:
        return abstract
    inverted = item.get("abstract_inverted_index", {})
    if not inverted:
        return ""
    max_pos = 0
    for positions in inverted.values():
        if positions:
            max_pos = max(max_pos, max(positions))
    words = [""] * (max_pos + 1)
    for word, positions in inverted.items():
        for pos in positions:
            if 0 <= pos < len(words):
                words[pos] = word
    return " ".join(words).strip()

