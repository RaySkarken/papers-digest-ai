from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

from papers_digest.models import Paper
from papers_digest.ranking import score_paper


@dataclass
class DigestMetrics:
    """Metrics for a single digest generation."""
    timestamp: str
    query: str
    target_date: str
    papers_found: int
    papers_ranked: int
    sources_used: int
    papers_per_source: dict[str, int] = field(default_factory=dict)
    avg_relevance_score: float = 0.0
    min_relevance_score: float = 0.0
    max_relevance_score: float = 0.0
    generation_time_seconds: float = 0.0
    source_errors: dict[str, str] = field(default_factory=dict)
    summarizer_used: str = "unknown"
    digest_length_chars: int = 0
    digest_parts_count: int = 0


@dataclass
class PostMetrics:
    """Metrics for a single post."""
    timestamp: str
    channel_id: str
    success: bool
    error_message: str = ""
    parts_sent: int = 0
    total_chars: int = 0


@dataclass
class SystemMetrics:
    """Overall system metrics."""
    total_digests: int = 0
    total_posts: int = 0
    successful_posts: int = 0
    failed_posts: int = 0
    total_papers_processed: int = 0
    avg_papers_per_digest: float = 0.0
    avg_generation_time: float = 0.0
    channels_count: int = 0
    sources_success_rate: dict[str, float] = field(default_factory=dict)
    uptime_start: str = ""
    last_digest_time: str = ""


class MetricsCollector:
    """Collect and store metrics."""
    
    def __init__(self, metrics_dir: str = "data/metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self._system_metrics = SystemMetrics()
        self._load_system_metrics()
    
    def record_digest(
        self,
        query: str,
        target_date: date,
        papers: Sequence[Paper],
        ranked: Sequence[Paper],
        sources_used: Sequence[str],
        papers_per_source: dict[str, int],
        source_errors: dict[str, str],
        generation_time: float,
        summarizer_name: str,
        digest_parts: Sequence[str],
    ) -> DigestMetrics:
        """Record metrics for a digest generation."""
        scores = [score_paper(query, paper) for paper in ranked] if ranked else [0.0]
        
        metrics = DigestMetrics(
            timestamp=datetime.now().isoformat(),
            query=query,
            target_date=target_date.isoformat(),
            papers_found=len(papers),
            papers_ranked=len(ranked),
            sources_used=len(sources_used),
            papers_per_source=papers_per_source,
            avg_relevance_score=sum(scores) / len(scores) if scores else 0.0,
            min_relevance_score=min(scores) if scores else 0.0,
            max_relevance_score=max(scores) if scores else 0.0,
            generation_time_seconds=generation_time,
            source_errors=source_errors,
            summarizer_used=summarizer_name,
            digest_length_chars=sum(len(part) for part in digest_parts),
            digest_parts_count=len(digest_parts),
        )
        
        self._save_digest_metrics(metrics)
        self._update_system_metrics(metrics)
        return metrics
    
    def record_post(
        self,
        channel_id: str,
        success: bool,
        parts_sent: int = 0,
        total_chars: int = 0,
        error_message: str = "",
    ) -> PostMetrics:
        """Record metrics for a post."""
        metrics = PostMetrics(
            timestamp=datetime.now().isoformat(),
            channel_id=channel_id,
            success=success,
            error_message=error_message,
            parts_sent=parts_sent,
            total_chars=total_chars,
        )
        
        self._save_post_metrics(metrics)
        self._update_post_metrics(metrics)
        return metrics
    
    def _save_digest_metrics(self, metrics: DigestMetrics) -> None:
        """Save digest metrics to file."""
        filename = f"digest_{date.today().isoformat()}.jsonl"
        filepath = self.metrics_dir / filename
        with filepath.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metrics), ensure_ascii=False) + "\n")
    
    def _save_post_metrics(self, metrics: PostMetrics) -> None:
        """Save post metrics to file."""
        filename = f"posts_{date.today().isoformat()}.jsonl"
        filepath = self.metrics_dir / filename
        with filepath.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metrics), ensure_ascii=False) + "\n")
    
    def _update_system_metrics(self, metrics: DigestMetrics) -> None:
        """Update system-wide metrics."""
        self._system_metrics.total_digests += 1
        self._system_metrics.total_papers_processed += metrics.papers_found
        self._system_metrics.last_digest_time = metrics.timestamp
        
        # Update averages
        if self._system_metrics.total_digests > 0:
            self._system_metrics.avg_papers_per_digest = (
                self._system_metrics.total_papers_processed / self._system_metrics.total_digests
            )
            # Calculate running average for generation time
            current_avg = self._system_metrics.avg_generation_time
            n = self._system_metrics.total_digests
            self._system_metrics.avg_generation_time = (
                (current_avg * (n - 1) + metrics.generation_time_seconds) / n
            )
        
        # Track source success rates
        for source, count in metrics.papers_per_source.items():
            if source not in self._system_metrics.sources_success_rate:
                self._system_metrics.sources_success_rate[source] = 0.0
        
        self._save_system_metrics()
    
    def _update_post_metrics(self, metrics: PostMetrics) -> None:
        """Update post metrics."""
        self._system_metrics.total_posts += 1
        if metrics.success:
            self._system_metrics.successful_posts += 1
        else:
            self._system_metrics.failed_posts += 1
        self._save_system_metrics()
    
    def _load_system_metrics(self) -> None:
        """Load system metrics from file."""
        filepath = self.metrics_dir / "system_metrics.json"
        if filepath.exists():
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                self._system_metrics = SystemMetrics(**data)
            except Exception:
                pass
    
    def _save_system_metrics(self) -> None:
        """Save system metrics to file."""
        filepath = self.metrics_dir / "system_metrics.json"
        filepath.write_text(
            json.dumps(asdict(self._system_metrics), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        return self._system_metrics
    
    def get_daily_summary(self, target_date: date | None = None) -> dict:
        """Get summary metrics for a specific day."""
        if target_date is None:
            target_date = date.today()
        
        digest_file = self.metrics_dir / f"digest_{target_date.isoformat()}.jsonl"
        posts_file = self.metrics_dir / f"posts_{target_date.isoformat()}.jsonl"
        
        digests = []
        if digest_file.exists():
            for line in digest_file.read_text(encoding="utf-8").strip().split("\n"):
                if line:
                    digests.append(json.loads(line))
        
        posts = []
        if posts_file.exists():
            for line in posts_file.read_text(encoding="utf-8").strip().split("\n"):
                if line:
                    posts.append(json.loads(line))
        
        return {
            "date": target_date.isoformat(),
            "digests_count": len(digests),
            "posts_count": len(posts),
            "successful_posts": sum(1 for p in posts if p.get("success", False)),
            "failed_posts": sum(1 for p in posts if not p.get("success", False)),
            "total_papers_found": sum(d.get("papers_found", 0) for d in digests),
            "total_papers_ranked": sum(d.get("papers_ranked", 0) for d in digests),
            "avg_relevance_score": (
                sum(d.get("avg_relevance_score", 0) for d in digests) / len(digests)
                if digests else 0.0
            ),
            "avg_generation_time": (
                sum(d.get("generation_time_seconds", 0) for d in digests) / len(digests)
                if digests else 0.0
            ),
            "sources_used": set(
                source
                for d in digests
                for source in d.get("papers_per_source", {}).keys()
            ),
        }


# Global metrics collector instance
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        import os
        metrics_dir = os.getenv("PAPERS_DIGEST_METRICS_DIR", "data/metrics")
        _metrics_collector = MetricsCollector(metrics_dir)
    return _metrics_collector

