from datetime import date

from papers_digest.models import Paper
from papers_digest.ranking import extract_keywords, rank_papers


def test_rank_papers_orders_by_query_match() -> None:
    papers = [
        Paper(
            paper_id="1",
            title="Graph networks for chemistry",
            abstract="We study molecule graphs.",
            authors=["A"],
            url="http://example.com/1",
            published_date=date(2026, 1, 22),
            source="unit",
        ),
        Paper(
            paper_id="2",
            title="Transformers for graph reasoning",
            abstract="Graph reasoning and transformers.",
            authors=["B"],
            url="http://example.com/2",
            published_date=date(2026, 1, 22),
            source="unit",
        ),
    ]

    ranked = rank_papers("graph transformers", papers, limit=2)
    assert ranked[0].paper_id == "2"


def test_extract_keywords_skips_query_terms() -> None:
    papers = [
        Paper(
            paper_id="1",
            title="Diffusion models for audio",
            abstract="Audio diffusion with transformer blocks.",
            authors=["A"],
            url="http://example.com/1",
            published_date=date(2026, 1, 22),
            source="unit",
        )
    ]
    keywords = extract_keywords("diffusion", papers, top_k=3)
    assert "diffusion" not in keywords

