from __future__ import annotations

from datetime import date
from typing import Iterable

import requests

from papers_digest.models import Paper
from papers_digest.sources.base import PaperSource


class SemanticScholarSource(PaperSource):
    name = "semantic_scholar"

    def fetch(self, target_date: date, query: str) -> Iterable[Paper]:
        target = target_date.strftime("%Y-%m-%d")
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query.strip() or "artificial intelligence",
            "limit": 50,
            "fields": "title,abstract,authors,url,publicationDate",
        }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json().get("data", [])

        for item in data:
            pub_date = item.get("publicationDate")
            if pub_date != target:
                continue
            yield Paper(
                paper_id=item.get("paperId", ""),
                title=item.get("title", ""),
                abstract=item.get("abstract", ""),
                authors=[author.get("name", "") for author in item.get("authors", [])],
                url=item.get("url", ""),
                published_date=target_date,
                source=self.name,
            )

