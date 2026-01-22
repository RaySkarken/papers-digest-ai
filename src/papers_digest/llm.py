from __future__ import annotations

import os
from typing import Sequence

from papers_digest.models import DigestItem


class LLMClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._client = None
        if self.api_key:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.api_key)
            except Exception:
                self._client = None

    def enabled(self) -> bool:
        return self._client is not None

    def summarize_items(self, query: str, items: Sequence[DigestItem]) -> list[str]:
        if not self._client:
            return [item.highlights for item in items]
        summaries: list[str] = []
        for item in items:
            prompt = (
                "Summarize the paper in 2-3 sentences. Focus on relevance to the query.\n"
                f"Query: {query}\nTitle: {item.paper.title}\nAbstract: {item.paper.abstract or ''}"
            )
            response = self._client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
            )
            summaries.append(response.output_text.strip())
        return summaries

    def recommendations(self, query: str, items: Sequence[DigestItem]) -> str:
        if not self._client:
            topics = ", ".join(item.paper.title for item in items[:3])
            return f"Обратите внимание на: {topics}"
        titles = "\n".join(f"- {item.paper.title}" for item in items)
        prompt = (
            "Write 3-5 bullet recommendations on what to pay attention to in today's papers."
            f"\nQuery: {query}\nPapers:\n{titles}"
        )
        response = self._client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        return response.output_text.strip()
