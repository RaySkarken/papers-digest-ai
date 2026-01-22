from __future__ import annotations

from datetime import date
from typing import Iterable, Sequence

from papers_digest.formatter import format_digest
from papers_digest.models import Paper
from papers_digest.ranking import extract_keywords, rank_papers
from papers_digest.sources.arxiv import ArxivSource
from papers_digest.sources.base import PaperSource
from papers_digest.sources.crossref import CrossrefSource
from papers_digest.sources.semantic_scholar import SemanticScholarSource
from papers_digest.summarizer import SimpleSummarizer, Summarizer


def _default_sources() -> list[PaperSource]:
    return [ArxivSource(), CrossrefSource(), SemanticScholarSource()]


def _collect_papers(target_date: date, sources: Sequence[PaperSource]) -> list[Paper]:
    papers: list[Paper] = []
    for source in sources:
        papers.extend(source.fetch(target_date))
    return papers


def run_digest(
    query: str,
    target_date: date,
    limit: int = 10,
    sources: Sequence[PaperSource] | None = None,
    summarizer: Summarizer | None = None,
) -> str:
    sources = list(sources) if sources is not None else _default_sources()
    summarizer = summarizer or SimpleSummarizer()

    papers = _collect_papers(target_date, sources)
    ranked = rank_papers(query, papers, limit)
    summaries = {paper.paper_id: summarizer.summarize(paper) for paper in ranked}
    keywords = extract_keywords(query, ranked)
    recommendations = [
        "Check novelty vs. prior art for the top 2 papers.",
        "Pay attention to evaluation datasets and ablation results.",
    ]
    if keywords:
        recommendations.append(f"Watch for themes: {', '.join(keywords)}.")

    return format_digest(query, target_date, ranked, summaries, recommendations)

