# Papers Digest AI

AI‑агент, который находит свежие научные статьи за сегодня из разных источников, фильтрует по запросу, делает подборку и рекомендации.

## Возможности
- Источники: arXiv, Crossref, Semantic Scholar.
- Фильтрация по дате (сегодня по умолчанию) и релевантности запросу.
- Ролевая архитектура: архитектор, разработчик, аналитик, тестировщик.
- Генерация digest‑поста и рекомендаций (LLM опционально).

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Пример запуска:
```bash
papers-digest --query "graph neural networks" --limit 10
```

## LLM (опционально)
Если задан `OPENAI_API_KEY`, агент аналитика будет использовать LLM для более качественных резюме и рекомендаций.

## Архитектура
См. `docs/architecture.md` и `docs/metrics.md`.

## Тесты
```bash
pip install -e .[test]
pytest
```

## Лицензия
MIT
