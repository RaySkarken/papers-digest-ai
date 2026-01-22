from __future__ import annotations

from datetime import date
from typing import Iterable

import requests

from papers_digest.models import Paper


class SemanticScholarSource:
    name = "Semantic Scholar"

    def __init__(self, limit: int = 50, timeout: float = 10.0) -> None:
        self.limit = limit
        self.timeout = timeout

    def search(self, query: str, target_date: date) -> Iterable[Paper]:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": self.limit,
            "fields": "title,abstract,url,authors,publicationDate",
        }
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json().get("data", [])
        for item in data:
            publication_date = item.get("publicationDate")
            if not publication_date:
                continue
            published = date.fromisoformat(publication_date)
            if published != target_date:
                continue
            authors = tuple(author.get("name", "").strip() for author in item.get("authors", []))
            yield Paper(
                title=item.get("title", "Untitled"),
                url=item.get("url", ""),
                published_date=published,
                abstract=item.get("abstract"),
                source=self.name,
                authors=tuple(name for name in authors if name),
            )
