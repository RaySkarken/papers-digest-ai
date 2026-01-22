from __future__ import annotations

from datetime import date
from typing import Sequence

from papers_digest.models import Paper


def format_digest(
    query: str,
    target_date: date,
    papers: Sequence[Paper],
    summaries: dict[str, str],
    recommendations: Sequence[str],
) -> str:
    lines = [
        f"# Papers digest for {target_date.isoformat()}",
        "",
        f"Query: **{query}**",
        "",
    ]

    if not papers:
        lines.append("No papers matched today.")
        return "\n".join(lines)

    lines.append("## Top papers")
    lines.append("")
    for idx, paper in enumerate(papers, start=1):
        summary = summaries.get(paper.paper_id, "Summary not available.")
        authors = ", ".join(paper.authors) if paper.authors else "Unknown authors"
        lines.extend(
            [
                f"{idx}. **{paper.title}**",
                f"   - Source: {paper.source}",
                f"   - Authors: {authors}",
                f"   - Link: {paper.url}",
                f"   - Summary: {summary}",
                "",
            ]
        )

    if recommendations:
        lines.append("## Recommendations")
        lines.append("")
        for item in recommendations:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"

