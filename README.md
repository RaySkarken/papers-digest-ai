# Papers Digest AI

AI agent that fetches today's newest papers from multiple sources, filters and ranks them by a user query, and produces a concise, interesting post with recommendations.

## Quick start

```
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
papers-digest run --query "multimodal retrieval" --limit 8
```

## What it does

- Collects papers from arXiv, Crossref, and Semantic Scholar released today.
- Filters by exact date and ranks by query relevance.
- Generates a markdown digest with short summaries and focus recommendations.

## Project structure

- `src/papers_digest/` core pipeline and source adapters.
- `docs/` architecture, roles, and quality metrics.
- `tests/` unit tests for ranking and pipeline.

## Configuration

Copy `.env.example` to `.env` and set keys if you want to enable optional LLM summarization later.

## Docs

- `docs/roles.md`
- `docs/architecture.md`
- `docs/metrics.md`

## Running tests

```
pytest
```

