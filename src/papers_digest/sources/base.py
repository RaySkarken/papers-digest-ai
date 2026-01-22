from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Iterable

from papers_digest.models import Paper


class PaperSource(ABC):
    name: str

    @abstractmethod
    def fetch(self, target_date: date) -> Iterable[Paper]:
        raise NotImplementedError

