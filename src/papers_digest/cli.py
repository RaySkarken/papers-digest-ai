from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from papers_digest.pipeline import run_digest


def _parse_date(value: str) -> date:
    if value.lower() == "today":
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate daily paper digests.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Generate a digest.")
    run_parser.add_argument("--query", required=True, help="User query for relevance.")
    run_parser.add_argument("--date", default="today", help="Date in YYYY-MM-DD or 'today'.")
    run_parser.add_argument("--limit", type=int, default=10, help="Max papers to include.")
    run_parser.add_argument("--output", help="Write digest to file.")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    target_date = _parse_date(args.date)

    digest = run_digest(args.query, target_date, args.limit)
    if args.output:
        Path(args.output).write_text(digest, encoding="utf-8")
    else:
        print(digest)


if __name__ == "__main__":
    main()

