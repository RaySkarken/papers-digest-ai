from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

from papers_digest.models import DigestItem, Paper

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _build_tf(tokens: Iterable[str]) -> Counter[str]:
    return Counter(tokens)


def score_paper(query: str, paper: Paper) -> float:
    query_tokens = _tokens(query)
    if not query_tokens:
        return 0.0
    content = " ".join([paper.title, paper.abstract or ""]).strip()
    content_tokens = _tokens(content)
    if not content_tokens:
        return 0.0
    query_tf = _build_tf(query_tokens)
    content_tf = _build_tf(content_tokens)
    overlap = sum(content_tf[token] for token in query_tf)
    length_norm = math.sqrt(len(content_tokens))
    return overlap / length_norm


def build_highlight(query: str, paper: Paper) -> str:
    query_tokens = set(_tokens(query))
    text = paper.abstract or paper.title
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentences:
        sentence_tokens = set(_tokens(sentence))
        if query_tokens & sentence_tokens:
            return sentence.strip()
    return (sentences[0].strip() if sentences and sentences[0] else paper.title)


def rank_papers(query: str, papers: Iterable[Paper], limit: int) -> list[DigestItem]:
    scored = [
        DigestItem(paper=paper, score=score_paper(query, paper), highlights=build_highlight(query, paper))
        for paper in papers
    ]
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:limit]
