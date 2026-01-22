from __future__ import annotations

from datetime import date
from typing import Iterable

import feedparser
import requests

from papers_digest.models import Paper


class ArxivSource:
    name = "arXiv"

    def __init__(self, max_results: int = 50, timeout: float = 10.0) -> None:
        self.max_results = max_results
        self.timeout = timeout

    def search(self, query: str, target_date: date) -> Iterable[Paper]:
        url = (
            "http://export.arxiv.org/api/query?"
            f"search_query=all:{query}&sortBy=submittedDate&sortOrder=descending"
            f"&max_results={self.max_results}"
        )
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        for entry in feed.entries:
            published = date.fromisoformat(entry.published[:10])
            if published != target_date:
                continue
            authors = tuple(author.name for author in entry.authors) if entry.get("authors") else ()
            yield Paper(
                title=entry.title.strip(),
                url=entry.link,
                published_date=published,
                abstract=entry.summary.strip() if entry.get("summary") else None,
                source=self.name,
                authors=authors,
            )
