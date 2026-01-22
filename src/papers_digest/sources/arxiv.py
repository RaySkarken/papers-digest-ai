from __future__ import annotations

from datetime import date
from typing import Iterable

import feedparser
import requests
from dateutil import parser as date_parser

from papers_digest.models import Paper
from papers_digest.sources.base import PaperSource


class ArxivSource(PaperSource):
    name = "arxiv"

    def fetch(self, target_date: date) -> Iterable[Paper]:
        query = "cat:cs.AI OR cat:cs.CL OR cat:cs.LG"
        url = (
            "http://export.arxiv.org/api/query?"
            f"search_query={query}&start=0&max_results=50&sortBy=submittedDate&sortOrder=descending"
        )
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        feed = feedparser.parse(response.text)
        for entry in feed.entries:
            published = date_parser.parse(entry.published).date()
            if published != target_date:
                continue
            yield Paper(
                paper_id=entry.id,
                title=entry.title.strip(),
                abstract=entry.summary.strip(),
                authors=[author.name for author in entry.authors],
                url=entry.link,
                published_date=published,
                source=self.name,
            )

