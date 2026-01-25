from datetime import date

from papers_digest.models import Paper
from papers_digest.pipeline import run_digest
from papers_digest.sources.base import PaperSource


class FakeSource(PaperSource):
    name = "fake"

    def __init__(self, papers: list[Paper]) -> None:
        self._papers = papers

    def fetch(self, target_date: date, query: str):
        return [paper for paper in self._papers if paper.published_date == target_date]


def test_run_digest_returns_list_of_messages() -> None:
    """Test that run_digest returns a list of Telegram messages."""
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

    digest_parts = run_digest(
        query="vision transformer",
        target_date=target_date,
        limit=3,
        sources=[FakeSource(papers)],
    )

    # run_digest returns list[str] for Telegram messages
    assert isinstance(digest_parts, list)
    assert len(digest_parts) >= 1
    
    # Join all parts to check content
    full_digest = "\n".join(digest_parts)
    
    # Check date is present (escaped for MarkdownV2)
    assert "2026" in full_digest
    assert "01" in full_digest
    assert "22" in full_digest
    
    # Check paper title is present (escaped for MarkdownV2)
    assert "Vision transformers today" in full_digest
    
    # Check query/area is mentioned
    assert "vision transformer" in full_digest


def test_run_digest_empty_sources() -> None:
    """Test that run_digest handles empty results gracefully."""
    target_date = date(2026, 1, 22)
    
    digest_parts = run_digest(
        query="nonexistent topic",
        target_date=target_date,
        limit=3,
        sources=[FakeSource([])],
    )
    
    assert isinstance(digest_parts, list)
    assert len(digest_parts) >= 1
    
    full_digest = "\n".join(digest_parts)
    # Should indicate no papers found (in Russian)
    assert "не найдено" in full_digest or "2026" in full_digest

