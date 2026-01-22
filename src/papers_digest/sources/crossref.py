from __future__ import annotations

from datetime import date
from typing import Iterable

import requests

from papers_digest.models import Paper
from papers_digest.sources.base import PaperSource


class CrossrefSource(PaperSource):
    name = "crossref"

    def fetch(self, target_date: date, query: str) -> Iterable[Paper]:
        target = target_date.strftime("%Y-%m-%d")
        url = "https://api.crossref.org/works"
        params = {
            "filter": f"from-pub-date:{target},until-pub-date:{target}",
            "query.title": query.strip() or "artificial intelligence",
            "rows": 50,
            "select": "DOI,title,author,URL,abstract,published-online,published-print",
        }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        items = response.json().get("message", {}).get("items", [])

        for item in items:
            title = (item.get("title") or [""])[0]
            abstract = (item.get("abstract") or "").replace("<jats:p>", "").replace("</jats:p>", "")
            authors = [
                f"{author.get('given', '').strip()} {author.get('family', '').strip()}".strip()
                for author in item.get("author", [])
                if author.get("family")
            ]
            if not title:
                continue
            yield Paper(
                paper_id=item.get("DOI", ""),
                title=title,
                abstract=abstract,
                authors=authors,
                url=item.get("URL", ""),
                published_date=target_date,
                source=self.name,
            )

