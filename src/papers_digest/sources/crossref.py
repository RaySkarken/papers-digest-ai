from __future__ import annotations

from datetime import date
from typing import Iterable

import requests

from papers_digest.models import Paper


class CrossrefSource:
    name = "Crossref"

    def __init__(self, rows: int = 50, timeout: float = 10.0) -> None:
        self.rows = rows
        self.timeout = timeout

    def search(self, query: str, target_date: date) -> Iterable[Paper]:
        date_str = target_date.isoformat()
        url = (
            "https://api.crossref.org/works?"
            f"query={query}&rows={self.rows}"
            f"&filter=from-pub-date:{date_str},until-pub-date:{date_str}"
        )
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        items = response.json().get("message", {}).get("items", [])
        for item in items:
            issued_parts = item.get("issued", {}).get("date-parts", [])
            if not issued_parts or not issued_parts[0]:
                continue
            year, month, day = (issued_parts[0] + [1, 1, 1])[:3]
            published = date(year, month, day)
            if published != target_date:
                continue
            title_parts = item.get("title", [])
            title = title_parts[0] if title_parts else "Untitled"
            authors = tuple(
                f"{person.get('given', '').strip()} {person.get('family', '').strip()}".strip()
                for person in item.get("author", [])
            )
            yield Paper(
                title=title,
                url=item.get("URL", ""),
                published_date=published,
                abstract=item.get("abstract"),
                source=self.name,
                authors=tuple(name for name in authors if name),
            )
