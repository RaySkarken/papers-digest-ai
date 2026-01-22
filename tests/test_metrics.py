from datetime import date

from papers_digest.metrics import build_metrics
from papers_digest.models import DigestItem, DigestReport, Paper


def test_build_metrics_non_empty():
    paper = Paper(
        title="Graph networks",
        url="http://example.com",
        published_date=date(2025, 1, 1),
        abstract="Summary",
        source="arXiv",
    )
    report = DigestReport(
        query="graph",
        run_date=date(2025, 1, 1),
        items=(DigestItem(paper=paper, score=1.0, highlights="summary"),),
        recommendations="Focus",
    )
    metrics = build_metrics(report)
    assert metrics["freshness"] == 1.0
    assert metrics["coverage"] > 0
    assert metrics["topic_diversity"] == 1.0
