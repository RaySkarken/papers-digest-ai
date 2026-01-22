from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable, Sequence

from papers_digest.models import Paper


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def score_paper(query: str, paper: Paper) -> float:
    query_terms = _tokenize(query)
    if not query_terms:
        return 0.0
    text = f"{paper.title} {paper.abstract}"
    tokens = _tokenize(text)
    counts = Counter(tokens)

    score = 0.0
    for term in query_terms:
        tf = counts.get(term, 0)
        if tf == 0:
            continue
        score += 1.0 + math.log(tf)
    return score


def rank_papers(query: str, papers: Iterable[Paper], limit: int) -> list[Paper]:
    scored = sorted(papers, key=lambda paper: score_paper(query, paper), reverse=True)
    return list(scored[:limit])


def extract_keywords(query: str, papers: Sequence[Paper], top_k: int = 5) -> list[str]:
    tokens: Counter[str] = Counter()
    for paper in papers:
        tokens.update(_tokenize(f"{paper.title} {paper.abstract}"))
    for term in _tokenize(query):
        tokens.pop(term, None)
    return [term for term, _ in tokens.most_common(top_k)]

