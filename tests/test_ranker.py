from datetime import date

from papers_digest.models import Paper
from papers_digest.ranker import build_highlight, rank_papers, score_paper


def test_score_paper_basic():
    paper = Paper(
        title="Graph neural networks for molecules",
        url="http://example.com",
        published_date=date(2025, 1, 1),
        abstract="We apply graph neural networks to molecules.",
        source="arXiv",
    )
    score = score_paper("graph neural networks", paper)
    assert score > 0


def test_build_highlight_prefers_query_sentence():
    paper = Paper(
        title="Title",
        url="http://example.com",
        published_date=date(2025, 1, 1),
        abstract="Unrelated. We study transformers for graphs.",
        source="arXiv",
    )
    highlight = build_highlight("transformers", paper)
    assert "transformers" in highlight.lower()


def test_rank_papers_limit():
    paper = Paper(
        title="Title",
        url="http://example.com",
        published_date=date(2025, 1, 1),
        abstract="Some content",
        source="arXiv",
    )
    ranked = rank_papers("content", [paper, paper], limit=1)
    assert len(ranked) == 1
