from __future__ import annotations

import os
import re
from typing import Protocol

import requests

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


class OpenAISummarizer:
    def __init__(self, api_key: str, model: str | None = None) -> None:
        self._api_key = api_key
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def summarize(self, paper: Paper) -> str:
        prompt = (
            "Summarize the following paper in 2-3 sentences. Focus on novelty, "
            "methods, and results.\n\n"
            f"Title: {paper.title}\n"
            f"Abstract: {paper.abstract}\n"
        )
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 180,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            return SimpleSummarizer().summarize(paper)

