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

### Quick start

```
export PAPERS_DIGEST_BOT_TOKEN="..."
export PAPERS_DIGEST_ADMIN_IDS="123456789"
export PAPERS_DIGEST_WEB_URL="https://your-domain.com"  # For Mini-App
papers-digest-bot
papers-digest-web  # In another terminal, or use a process manager
```

### Mini-App (Web Interface)

The easiest way to manage channels is through the Telegram Mini-App:

1. Start the web server: `papers-digest-web`
2. Configure the Mini-App URL in BotFather:
   - Go to @BotFather
   - Use `/newapp` or `/myapps` → select your bot
   - Set the Mini-App URL to your web server URL
3. Use `/app` command in the bot to open the Mini-App

The Mini-App provides a user-friendly interface for:
- Adding/removing channels
- Setting science areas for each channel
- Configuring post times
- Managing LLM settings

### Bot Commands

- `/app` - Open Mini-App (recommended)
- `/channels` - List all channels
- `/add_channel <@channel> [area]` - Add a channel
- `/remove_channel <@channel>` - Remove a channel
- `/channel_info <@channel>` - Show channel info
- `/channel_set_area <@channel> <area>` - Set science area
- `/channel_set_time <@channel> <HH:MM>` - Set post time
- `/preview_today [@channel]` - Preview digest
- `/post_today [@channel]` - Post to channel

## What it does

- Collects papers from arXiv, Crossref, Semantic Scholar, and OpenAlex released today.
- Filters by exact date and ranks by query relevance.
- Generates a markdown digest with short summaries and focus recommendations.

## Project structure

- `src/papers_digest/` core pipeline and source adapters.
- `docs/` architecture, roles, and quality metrics.
- `tests/` unit tests for ranking and pipeline.

## Configuration

Use environment variables:

**Bot:**
- `PAPERS_DIGEST_BOT_TOKEN` - Telegram bot token (required)
- `PAPERS_DIGEST_ADMIN_IDS` - Comma-separated Telegram user IDs (required)
- `PAPERS_DIGEST_SETTINGS` - Optional path to settings JSON
- `PAPERS_DIGEST_TIMEZONE` - IANA timezone (default: `UTC`)

**Web Server (Mini-App):**
- `PAPERS_DIGEST_WEB_URL` - Public URL of your web server (required for Mini-App)
- `PAPERS_DIGEST_WEB_HOST` - Host to bind (default: `127.0.0.1`)
- `PAPERS_DIGEST_WEB_PORT` - Port to bind (default: `5000`)

**LLM:**
- `OPENAI_API_KEY` - Optional, for OpenAI summarization
- `OPENAI_MODEL` - Optional (default: `gpt-4o-mini`)
- `OLLAMA_MODEL` - Optional (default: `llama3.1:8b`)
- `OLLAMA_BASE_URL` - Optional (default: `http://localhost:11434`)

## Docs

- `docs/roles.md`
- `docs/architecture.md`
- `docs/metrics.md`

## Running tests

```
pytest
```

