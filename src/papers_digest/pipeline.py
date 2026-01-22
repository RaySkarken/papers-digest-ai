from __future__ import annotations

import os
from datetime import date
from typing import Iterable, Sequence

from papers_digest.formatter import format_digest
from papers_digest.models import Paper
from papers_digest.ranking import extract_keywords, rank_papers
from papers_digest.sources.arxiv import ArxivSource
from papers_digest.sources.base import PaperSource
from papers_digest.sources.crossref import CrossrefSource
from papers_digest.sources.openalex import OpenAlexSource
from papers_digest.sources.semantic_scholar import SemanticScholarSource
from papers_digest.summarizer import OpenAISummarizer, SimpleSummarizer, Summarizer


def _default_sources() -> list[PaperSource]:
    return [ArxivSource(), CrossrefSource(), SemanticScholarSource(), OpenAlexSource()]


def _collect_papers(target_date: date, query: str, sources: Sequence[PaperSource]) -> list[Paper]:
    papers: list[Paper] = []
    for source in sources:
        papers.extend(source.fetch(target_date, query))
    return papers


def run_digest(
    query: str,
    target_date: date,
    limit: int = 10,
    sources: Sequence[PaperSource] | None = None,
    summarizer: Summarizer | None = None,
) -> str:
    sources = list(sources) if sources is not None else _default_sources()
    if summarizer is None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        summarizer = OpenAISummarizer(api_key) if api_key else SimpleSummarizer()

    papers = _collect_papers(target_date, query, sources)
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

