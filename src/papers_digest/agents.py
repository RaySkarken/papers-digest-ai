from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Sequence

from papers_digest.llm import LLMClient
from papers_digest.models import DigestItem, DigestReport, Paper, unique_by_url
from papers_digest.ranker import rank_papers
from papers_digest.sources import ArxivSource, CrossrefSource, SemanticScholarSource


@dataclass(frozen=True)
class ArchitectPlan:
    query: str
    run_date: date
    limit: int
    sources: tuple[str, ...]


class ArchitectAgent:
    def build_plan(self, query: str, run_date: date, limit: int) -> ArchitectPlan:
        sources = ("arXiv", "Crossref", "Semantic Scholar")
        return ArchitectPlan(query=query, run_date=run_date, limit=limit, sources=sources)


class DeveloperAgent:
    def __init__(self) -> None:
        self.sources = [ArxivSource(), CrossrefSource(), SemanticScholarSource()]

    def fetch_papers(self, plan: ArchitectPlan) -> list[Paper]:
        papers: list[Paper] = []
        for source in self.sources:
            if source.name not in plan.sources:
                continue
            papers.extend(list(source.search(plan.query, plan.run_date)))
        return unique_by_url(papers)


class AnalystAgent:
    def __init__(self) -> None:
        self.llm = LLMClient()

    def analyze(self, plan: ArchitectPlan, papers: Iterable[Paper]) -> DigestReport:
        ranked = rank_papers(plan.query, papers, plan.limit)
        summaries = self.llm.summarize_items(plan.query, ranked)
        items: list[DigestItem] = []
        for item, summary in zip(ranked, summaries, strict=False):
            items.append(DigestItem(paper=item.paper, score=item.score, highlights=summary))
        recommendations = self.llm.recommendations(plan.query, items)
        return DigestReport(query=plan.query, run_date=plan.run_date, items=tuple(items), recommendations=recommendations)


class TesterAgent:
    def validate(self, report: DigestReport, min_items: int = 3) -> list[str]:
        issues: list[str] = []
        if len(report.items) < min_items:
            issues.append("Слишком мало статей в подборке.")
        if not report.top_sources():
            issues.append("Нет источников в выдаче.")
        if any(not item.paper.url for item in report.items):
            issues.append("Есть статьи без URL.")
        return issues


class AgentTeam:
    def __init__(self) -> None:
        self.architect = ArchitectAgent()
        self.developer = DeveloperAgent()
        self.analyst = AnalystAgent()
        self.tester = TesterAgent()

    def run(self, query: str, run_date: date, limit: int) -> tuple[DigestReport, Sequence[str]]:
        plan = self.architect.build_plan(query, run_date, limit)
        papers = self.developer.fetch_papers(plan)
        report = self.analyst.analyze(plan, papers)
        issues = self.tester.validate(report)
        return report, issues
