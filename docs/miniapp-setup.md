# Настройка Telegram Mini-App

## Варианты развертывания

### 1. Локальная разработка с ngrok (самый простой)

1. Установи ngrok: https://ngrok.com/download
2. Запусти веб-сервер:
   ```bash
   papers-digest-web
   ```
3. В другом терминале запусти ngrok:
   ```bash
   ngrok http 5000
   ```
4. Скопируй HTTPS URL из ngrok (например: `https://abc123.ngrok.io`)
5. Установи переменную окружения:
   ```bash
   export PAPERS_DIGEST_WEB_URL="https://abc123.ngrok.io"
   ```
6. Настрой в BotFather:
   - `/newapp` или `/myapps` → выбери бота
   - Установи Mini-App URL на URL из ngrok

**Примечание:** URL ngrok меняется при каждом перезапуске (на бесплатном тарифе). Для постоянного URL нужен платный план.

### 2. Облачные сервисы (бесплатные варианты)

#### Railway.app
1. Создай аккаунт на https://railway.app
2. Создай новый проект
3. Подключи GitHub репозиторий
4. Добавь переменные окружения:
   - `PAPERS_DIGEST_BOT_TOKEN`
   - `PAPERS_DIGEST_ADMIN_IDS`
   - `PAPERS_DIGEST_WEB_URL` (Railway предоставит URL автоматически)
5. Railway автоматически развернет и даст публичный URL

#### Render.com
1. Создай аккаунт на https://render.com
2. Создай новый Web Service
3. Подключи GitHub репозиторий
4. Настрой:
   - Build Command: `pip install -e .`
   - Start Command: `papers-digest-web`
5. Добавь переменные окружения
6. Render даст публичный URL

### 3. VPS с доменом

Если у тебя есть VPS и домен:
1. Настрой домен с SSL сертификатом (Let's Encrypt)
2. Установи приложение на VPS
3. Настрой reverse proxy (nginx) для проксирования на Flask
4. Используй домен как `PAPERS_DIGEST_WEB_URL`

## Без публичного сервера

Если не хочешь настраивать публичный сервер, можно использовать команды бота:
- `/channels` - список каналов
- `/add_channel` - добавить канал
- `/channel_set_area` - установить область
- И т.д.

Mini-App - это удобный интерфейс, но не обязательный.

