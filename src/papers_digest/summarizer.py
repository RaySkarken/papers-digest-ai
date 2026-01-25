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
        return summary or "Краткое содержание недоступно."


class OpenAISummarizer:
    def __init__(self, api_key: str, model: str | None = None) -> None:
        self._api_key = api_key
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def summarize(self, paper: Paper) -> str:
        prompt = (
            "Сделай краткое содержание следующей статьи на русском языке в 2-3 предложениях. "
            "Сосредоточься на новизне, методах и результатах.\n\n"
            f"Название: {paper.title}\n"
            f"Аннотация: {paper.abstract}\n"
        )
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": "Ты помощник, который делает краткие содержания научных статей на русском языке."},
                        {"role": "user", "content": prompt}
                    ],
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


class OllamaSummarizer:
    def __init__(self, model: str | None = None) -> None:
        self._model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self._base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def summarize(self, paper: Paper) -> str:
        prompt = (
            "Сделай краткое содержание следующей статьи на русском языке в 2-3 предложениях. "
            "Сосредоточься на новизне, методах и результатах.\n\n"
            f"Название: {paper.title}\n"
            f"Аннотация: {paper.abstract}\n"
        )
        try:
            response = requests.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                    "system": "Ты помощник, который делает краткие содержания научных статей на русском языке.",
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip() or SimpleSummarizer().summarize(paper)
        except Exception:
            return SimpleSummarizer().summarize(paper)

