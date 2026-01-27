from __future__ import annotations

import logging
import os
import time
from datetime import date
from typing import Iterable, Sequence

from papers_digest.formatter import format_digest
from papers_digest.metrics import get_metrics_collector
from papers_digest.models import Paper
from papers_digest.ranking import extract_keywords, rank_papers
from papers_digest.sources.arxiv import ArxivSource
from papers_digest.sources.base import PaperSource
from papers_digest.sources.crossref import CrossrefSource
from papers_digest.sources.openalex import OpenAlexSource
from papers_digest.sources.semantic_scholar import SemanticScholarSource
from papers_digest.summarizer import OpenAISummarizer, SimpleSummarizer, Summarizer

logger = logging.getLogger(__name__)


def _default_sources() -> list[PaperSource]:
    return [ArxivSource(), CrossrefSource(), SemanticScholarSource(), OpenAlexSource()]


def _collect_papers(target_date: date, query: str, sources: Sequence[PaperSource]) -> tuple[list[Paper], dict[str, int], dict[str, str]]:
    """Collect papers from sources and return papers, papers_per_source, and source_errors."""
    papers: list[Paper] = []
    papers_per_source: dict[str, int] = {}
    source_errors: dict[str, str] = {}
    
    for source in sources:
        try:
            fetched = list(source.fetch(target_date, query))
            papers.extend(fetched)
            papers_per_source[source.name] = len(fetched)
            logger.info(f"Fetched {len(fetched)} papers from {source.name}")
        except Exception as e:
            error_msg = str(e)
            source_errors[source.name] = error_msg
            papers_per_source[source.name] = 0
            logger.warning(f"Failed to fetch from {source.name}: {e}", exc_info=True)
            continue
    return papers, papers_per_source, source_errors


def run_digest(
    query: str,
    target_date: date,
    limit: int = 10,
    sources: Sequence[PaperSource] | None = None,
    summarizer: Summarizer | None = None,
    collect_metrics: bool = True,
) -> list[str]:
    """Run digest and return list of message parts for Telegram."""
    start_time = time.time()
    sources = list(sources) if sources is not None else _default_sources()
    if summarizer is None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        summarizer = OpenAISummarizer(api_key) if api_key else SimpleSummarizer()
    
    summarizer_name = summarizer.__class__.__name__

    papers, papers_per_source, source_errors = _collect_papers(target_date, query, sources)
    ranked = rank_papers(query, papers, limit)
    summaries = {paper.paper_id: summarizer.summarize(paper) for paper in ranked}
    digest_parts = format_digest(query, target_date, ranked, summaries, [])
    
    generation_time = time.time() - start_time
    
    # Collect metrics
    if collect_metrics:
        try:
            metrics = get_metrics_collector()
            metrics.record_digest(
                query=query,
                target_date=target_date,
                papers=papers,
                ranked=ranked,
                sources_used=[s.name for s in sources],
                papers_per_source=papers_per_source,
                source_errors=source_errors,
                generation_time=generation_time,
                summarizer_name=summarizer_name,
                digest_parts=digest_parts,
            )
        except Exception as e:
            logger.warning(f"Failed to record metrics: {e}", exc_info=True)
    
    return digest_parts

