from __future__ import annotations

import re
from typing import Protocol

from papers_digest.models import Paper


class Summarizer(Protocol):
    def summarize(self, paper: Paper) -> str:
        raise NotImplementedError


class SimpleSummarizer:
    def summarize(self, paper: Paper) -> str:
        abstract = paper.abstract or ""
        sentences = re.split(r"(?<=[.!?])\s+", abstract.strip())
        summary = " ".join(sentences[:2]).strip()
        return summary or "Summary not available."

