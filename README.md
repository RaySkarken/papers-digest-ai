# Papers Digest AI

AI-агент для автоматического сбора, ранжирования и публикации научных статей в Telegram-каналы.

## Возможности

- **Множество источников**: arXiv, Crossref, Semantic Scholar, OpenAlex
- **Интеллектуальное ранжирование**: фильтрация и ранжирование статей по релевантности к заданной области науки
- **Генерация саммари**: краткие аннотации через OpenAI, Ollama или простой алгоритм
- **Telegram-бот**: административный бот для управления каналами
- **Mini-App**: веб-интерфейс для удобного управления настройками
- **Мультиканальность**: поддержка нескольких каналов с индивидуальными настройками
- **Автопостинг**: планировщик автоматической публикации по расписанию

## Быстрый старт

### Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### CLI-использование

```bash
# Генерация дайджеста в консоль
papers-digest run --query "multimodal retrieval" --limit 8

# Генерация за определённую дату
papers-digest run --query "machine learning" --date 2025-01-20 --limit 10

# Сохранение в файл
papers-digest run --query "computer vision" --output digest.md
```

### Telegram-бот

```bash
export PAPERS_DIGEST_BOT_TOKEN="ваш_токен"
export PAPERS_DIGEST_ADMIN_IDS="123456789"
export PAPERS_DIGEST_WEB_URL="https://your-domain.com"  # Для Mini-App
papers-digest-bot
```

### Веб-сервер (Mini-App)

```bash
papers-digest-web  # В отдельном терминале
```

## Архитектура

### Основные модули

| Модуль | Описание |
|--------|----------|
| `sources/` | Адаптеры для сбора статей из различных API |
| `pipeline.py` | Оркестрация: сбор → фильтрация → ранжирование → саммари → форматирование |
| `ranking.py` | Скоринг релевантности статей к запросу |
| `summarizer.py` | Генерация аннотаций (OpenAI, Ollama, простой алгоритм) |
| `formatter.py` | Форматирование дайджеста в Markdown/Telegram |
| `bot.py` | Telegram-бот с админ-командами |
| `webapp.py` | Flask-сервер для Mini-App |
| `settings.py` | Хранение настроек каналов |

### Поток данных

1. Адаптеры источников получают статьи из API (arXiv, Crossref, Semantic Scholar, OpenAlex)
2. Нормализация в модель `Paper`
3. Фильтрация по дате публикации
4. Ранжирование по релевантности к запросу
5. Генерация аннотаций
6. Форматирование в пост
7. Публикация в канал (вручную или по расписанию)

## Конфигурация

### Переменные окружения

#### Telegram-бот

| Переменная | Описание | Обязательность |
|------------|----------|----------------|
| `PAPERS_DIGEST_BOT_TOKEN` | Токен Telegram-бота | Да |
| `PAPERS_DIGEST_ADMIN_IDS` | ID администраторов (через запятую) | Да |
| `PAPERS_DIGEST_SETTINGS` | Путь к файлу настроек JSON | Нет |
| `PAPERS_DIGEST_TIMEZONE` | Часовой пояс IANA (по умолчанию: `UTC`) | Нет |

#### Веб-сервер (Mini-App)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `PAPERS_DIGEST_WEB_URL` | Публичный URL веб-сервера | — |
| `PAPERS_DIGEST_WEB_HOST` | Хост для привязки | `127.0.0.1` |
| `PAPERS_DIGEST_WEB_PORT` | Порт для привязки | `5000` |

#### LLM-провайдеры

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `OPENAI_API_KEY` | API-ключ OpenAI | — |
| `OPENAI_MODEL` | Модель OpenAI | `gpt-4o-mini` |
| `OLLAMA_MODEL` | Модель Ollama | `llama3.1:8b` |
| `OLLAMA_BASE_URL` | URL Ollama | `http://localhost:11434` |

## Команды бота

### Управление каналами

| Команда | Описание |
|---------|----------|
| `/app` | Открыть Mini-App (рекомендуется) |
| `/channels` | Список всех каналов |
| `/add_channel <@channel> [область]` | Добавить канал |
| `/remove_channel <@channel>` | Удалить канал |
| `/channel_info <@channel>` | Информация о канале |
| `/channel_set_area <@channel> <область>` | Установить область науки |
| `/channel_set_time <@channel> <HH:MM>` | Установить время публикации |

### Публикация

| Команда | Описание |
|---------|----------|
| `/preview_today [@channel]` | Предпросмотр дайджеста |
| `/post_today [@channel]` | Опубликовать в канал |

### Настройки LLM

| Команда | Описание |
|---------|----------|
| `/enable_llm` | Включить LLM-саммаризацию |
| `/disable_llm` | Выключить LLM-саммаризацию |
| `/set_summarizer auto\|openai\|ollama\|simple` | Выбрать провайдер |

### Расписание

| Команда | Описание |
|---------|----------|
| `/set_post_time HH:MM` | Установить время автопостинга |
| `/disable_post_time` | Отключить автопостинг |

## Mini-App

Telegram Mini-App предоставляет удобный веб-интерфейс для управления каналами.

### Настройка

1. Запустите веб-сервер: `papers-digest-web`
2. Настройте публичный URL (например, через ngrok или reverse proxy)
3. Установите `PAPERS_DIGEST_WEB_URL`
4. В @BotFather: `/myapps` → выберите бота → установите URL Mini-App
5. Используйте `/app` в боте для открытия интерфейса

### Функции Mini-App

- Просмотр списка каналов
- Добавление и удаление каналов
- Настройка области науки для каждого канала
- Управление временем публикации
- Настройка LLM-параметров

## Расширяемость

### Добавление нового источника

Реализуйте интерфейс `PaperSource`:

```python
from papers_digest.sources.base import PaperSource
from papers_digest.models import Paper

class MySource(PaperSource):
    @property
    def name(self) -> str:
        return "my_source"

    def fetch(self, target_date: date, query: str) -> Iterable[Paper]:
        # Реализация получения статей
        ...
```

### Добавление нового саммаризатора

Реализуйте интерфейс `Summarizer`:

```python
from papers_digest.summarizer import Summarizer
from papers_digest.models import Paper

class MySummarizer(Summarizer):
    def summarize(self, paper: Paper) -> str:
        # Реализация генерации аннотации
        ...
```

## Структура проекта

```
papers-digest-ai/
├── src/papers_digest/
│   ├── __init__.py
│   ├── __main__.py
│   ├── bot.py           # Telegram-бот
│   ├── cli.py           # CLI-интерфейс
│   ├── formatter.py     # Форматирование дайджеста
│   ├── models.py        # Модели данных (Paper)
│   ├── pipeline.py      # Главный пайплайн
│   ├── ranking.py       # Ранжирование статей
│   ├── settings.py      # Управление настройками
│   ├── summarizer.py    # Саммаризаторы
│   ├── webapp.py        # Flask Mini-App
│   └── sources/
│       ├── base.py      # Базовый класс источника
│       ├── arxiv.py     # arXiv API
│       ├── crossref.py  # Crossref API
│       ├── openalex.py  # OpenAlex API
│       └── semantic_scholar.py  # Semantic Scholar API
├── tests/
│   ├── test_pipeline.py
│   ├── test_ranking.py
│   └── test_settings.py
├── docs/
│   ├── architecture.md
│   ├── metrics.md
│   ├── miniapp-setup.md
│   └── roles.md
├── pyproject.toml
└── README.md
```

## Зависимости

- Python >= 3.10
- requests >= 2.31.0
- python-dateutil >= 2.9.0
- feedparser >= 6.0.11
- python-telegram-bot >= 21.0
- apscheduler >= 3.10.0
- flask >= 3.0.0

## Тестирование

```bash
pytest
```

## Документация

- [Архитектура](docs/architecture.md)
- [Метрики качества](docs/metrics.md)
- [Настройка Mini-App](docs/miniapp-setup.md)
- [Роли](docs/roles.md)

## Лицензия

MIT
