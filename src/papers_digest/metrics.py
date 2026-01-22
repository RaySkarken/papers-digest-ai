from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from papers_digest.models import DigestReport

SOURCES = ("arXiv", "Crossref", "Semantic Scholar")
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def freshness(report: DigestReport) -> float:
    if not report.items:
        return 0.0
    matches = sum(1 for item in report.items if item.paper.published_date == report.run_date)
    return matches / len(report.items)


def coverage(report: DigestReport, expected_sources: Iterable[str] = SOURCES) -> float:
    expected = set(expected_sources)
    if not expected:
        return 0.0
    return len(report.top_sources() & expected) / len(expected)


def topic_diversity(report: DigestReport) -> float:
    if not report.items:
        return 0.0
    top_terms = []
    for item in report.items:
        tokens = [t.lower() for t in _TOKEN_RE.findall(item.paper.title)]
        if not tokens:
            continue
        top_terms.append(Counter(tokens).most_common(1)[0][0])
    if not top_terms:
        return 0.0
    return len(set(top_terms)) / len(top_terms)


def build_metrics(report: DigestReport) -> dict[str, float]:
    return {
        "freshness": freshness(report),
        "coverage": coverage(report),
        "topic_diversity": topic_diversity(report),
    }
