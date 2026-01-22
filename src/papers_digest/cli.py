from __future__ import annotations

from datetime import date

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from papers_digest.agents import AgentTeam

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    query: str = typer.Option(..., "--query", "-q", help="Search query for today's papers"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max number of papers to include"),
    run_date: date = typer.Option(date.today(), "--date", "-d", help="Date for papers (YYYY-MM-DD)"),
) -> None:
    team = AgentTeam()
    report, issues = team.run(query=query, run_date=run_date, limit=limit)

    table = Table(title=f"Papers Digest for {report.run_date}")
    table.add_column("Score", justify="right")
    table.add_column("Title")
    table.add_column("Source", justify="center")
    table.add_column("URL")

    for item in report.items:
        table.add_row(f"{item.score:.2f}", item.paper.title, item.paper.source, item.paper.url)

    console.print(table)

    for item in report.items:
        console.print(Panel(item.highlights, title=item.paper.title, subtitle=item.paper.source))

    console.print(Panel(report.recommendations, title="Recommendations"))

    if issues:
        console.print(Panel("\n".join(issues), title="QA Warnings", style="red"))


if __name__ == "__main__":
    app()
