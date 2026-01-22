from datetime import date

from papers_digest.models import Paper
from papers_digest.pipeline import run_digest
from papers_digest.sources.base import PaperSource


class FakeSource(PaperSource):
    name = "fake"

    def __init__(self, papers: list[Paper]) -> None:
        self._papers = papers

    def fetch(self, target_date: date):
        return [paper for paper in self._papers if paper.published_date == target_date]


def test_run_digest_returns_markdown() -> None:
    target_date = date(2026, 1, 22)
    papers = [
        Paper(
            paper_id="1",
            title="Vision transformers today",
            abstract="We introduce a new vision transformer.",
            authors=["A"],
            url="http://example.com/1",
            published_date=target_date,
            source="fake",
        )
    ]

    digest = run_digest(
        query="vision transformer",
        target_date=target_date,
        limit=3,
        sources=[FakeSource(papers)],
    )

    assert "# Papers digest for 2026-01-22" in digest
    assert "Vision transformers today" in digest
    assert "Recommendations" in digest

