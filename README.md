# Papers Digest AI

AI agent that fetches today's newest papers from multiple sources, filters and ranks them by a user query, and produces a concise, interesting post with recommendations.

## Quick start

```
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
papers-digest run --query "multimodal retrieval" --limit 8
```

## Telegram bot admin

Admin commands are only available in private chat and require admin IDs.

```
export PAPERS_DIGEST_BOT_TOKEN="..."
export PAPERS_DIGEST_ADMIN_IDS="123456789"
export PAPERS_DIGEST_CHANNEL_ID="@your_channel"
papers-digest-bot
```

Admin commands:

- `/set_area <science area>` sets the science area for today.
- `/show_area` shows the current area.
- `/set_channel <@channel or id>` sets the target channel.
- `/preview_today` generates a draft message.
- `/post_today` posts to the channel.

## What it does

- Collects papers from arXiv, Crossref, and Semantic Scholar released today.
- Filters by exact date and ranks by query relevance.
- Generates a markdown digest with short summaries and focus recommendations.

## Project structure

- `src/papers_digest/` core pipeline and source adapters.
- `docs/` architecture, roles, and quality metrics.
- `tests/` unit tests for ranking and pipeline.

## Configuration

Use environment variables for the bot:

- `PAPERS_DIGEST_BOT_TOKEN`
- `PAPERS_DIGEST_ADMIN_IDS` (comma-separated Telegram user IDs)
- `PAPERS_DIGEST_CHANNEL_ID`
- `PAPERS_DIGEST_SETTINGS` (optional path to settings JSON)

## Docs

- `docs/roles.md`
- `docs/architecture.md`
- `docs/metrics.md`

## Running tests

```
pytest
```

