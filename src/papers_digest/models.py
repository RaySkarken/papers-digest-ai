from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence


@dataclass(frozen=True)
class Paper:
    paper_id: str
    title: str
    abstract: str
    authors: Sequence[str]
    url: str
    published_date: date
    source: str

