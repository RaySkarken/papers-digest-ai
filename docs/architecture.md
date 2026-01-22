# Architecture

## Goals

- Fetch papers from multiple sources released today.
- Rank by relevance to a user query.
- Produce a readable daily digest with recommendations.

## Modules

- `sources/*`: adapters to fetch papers and normalize fields.
- `pipeline.py`: orchestration of fetch, filter, rank, summarize, format.
- `ranking.py`: query relevance scoring.
- `summarizer.py`: short summaries, optional LLM.
- `formatter.py`: digest output in markdown.
- `cli.py`: user entrypoint.
- `bot.py`: Telegram bot with admin controls.
- `settings.py`: settings storage for admin config.

## Data flow

1. Sources fetch raw papers from APIs.
2. Normalize into `Paper` model.
3. Filter by target date.
4. Rank by relevance to query.
5. Summarize and format into a post.
6. Admin bot posts to the channel.
7. Scheduler can auto-post daily.

## Extensibility

- New sources: implement `PaperSource`.
- New ranking: implement `rank_papers`.
- New summarizer: implement `Summarizer` interface.

