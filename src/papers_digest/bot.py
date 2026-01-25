from __future__ import annotations

import os
from datetime import date
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import Application, CommandHandler, ContextTypes

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from papers_digest.pipeline import run_digest
from papers_digest.settings import Settings, load_settings, save_settings
from papers_digest.summarizer import OllamaSummarizer, OpenAISummarizer, SimpleSummarizer, Summarizer

_SCHEDULER: AsyncIOScheduler | None = None


def _admin_ids() -> set[int]:
    raw = os.getenv("PAPERS_DIGEST_ADMIN_IDS", "")
    return {int(value) for value in raw.split(",") if value.strip().isdigit()}


def _is_admin(update: Update) -> bool:
    if update.effective_chat is None or update.effective_user is None:
        return False
    if update.effective_chat.type != ChatType.PRIVATE:
        return False
    return update.effective_user.id in _admin_ids()


async def _require_admin(update: Update) -> bool:
    if _is_admin(update):
        return True
    if update.message:
        await update.message.reply_text("Access denied. Contact the admin.")
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    await update.message.reply_text(
        "Admin panel ready. Commands: /set_area, /show_area, /set_channel, /status, "
        "/preview_today, /post_today, /set_post_time, /disable_post_time, "
        "/enable_llm, /disable_llm, /set_summarizer"
    )


async def set_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Usage: /set_area <science area>")
        return
    settings = load_settings()
    settings.science_area = text
    save_settings(settings)
    await update.message.reply_text(f"Science area set to: {text}")


async def show_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    area = settings.science_area or "Not set"
    await update.message.reply_text(f"Science area: {area}")


async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Usage: /set_channel <channel_id or @channel>")
        return
    settings = load_settings()
    settings.channel_id = text
    save_settings(settings)
    await update.message.reply_text(f"Channel set to: {text}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    area = settings.science_area or "Not set"
    channel = settings.channel_id or os.getenv("PAPERS_DIGEST_CHANNEL_ID", "") or "Not set"
    post_time = settings.post_time or "Not set"
    llm_enabled = "on" if settings.use_llm else "off"
    summarizer = settings.summarizer_provider
    await update.message.reply_text(
        f"Science area: {area}\nChannel: {channel}\nPost time: {post_time}\n"
        f"LLM: {llm_enabled}\nSummarizer: {summarizer}"
    )

def _pick_summarizer(settings: Settings) -> Summarizer:
    api_key = os.getenv("OPENAI_API_KEY", "")
    provider = settings.summarizer_provider or "auto"
    if settings.use_llm and provider == "openai" and api_key:
        return OpenAISummarizer(api_key)
    if settings.use_llm and provider == "ollama":
        return OllamaSummarizer()
    if settings.use_llm and provider == "auto":
        if api_key:
            return OpenAISummarizer(api_key)
        return OllamaSummarizer()
    return SimpleSummarizer()


def _build_digest(settings: Settings) -> str:
    query = settings.science_area.strip()
    if not query:
        raise ValueError("Science area is not set. Use /set_area.")
    return run_digest(query=query, target_date=date.today(), limit=8, summarizer=_pick_summarizer(settings))


async def preview_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    try:
        digest = _build_digest(settings)
    except ValueError as exc:
        await update.message.reply_text(str(exc))
        return
    await update.message.reply_text(digest[:4096])


async def post_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    channel = settings.channel_id or os.getenv("PAPERS_DIGEST_CHANNEL_ID", "")
    if not channel:
        await update.message.reply_text("Channel is not set. Use /set_channel.")
        return
    try:
        digest = _build_digest(settings)
    except ValueError as exc:
        await update.message.reply_text(str(exc))
        return
    await context.bot.send_message(chat_id=channel, text=digest[:4096])
    await update.message.reply_text("Posted to channel.")


def _parse_time(value: str) -> tuple[int, int] | None:
    parts = value.split(":")
    if len(parts) != 2:
        return None
    hour, minute = parts[0].strip(), parts[1].strip()
    if not hour.isdigit() or not minute.isdigit():
        return None
    hour_i, minute_i = int(hour), int(minute)
    if hour_i < 0 or hour_i > 23 or minute_i < 0 or minute_i > 59:
        return None
    return hour_i, minute_i


async def set_post_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    value = " ".join(context.args).strip()
    parsed = _parse_time(value)
    if not parsed:
        await update.message.reply_text("Usage: /set_post_time HH:MM (24h)")
        return
    settings = load_settings()
    settings.post_time = value
    save_settings(settings)
    _reschedule(context.application)
    await update.message.reply_text(f"Post time set to: {value}")


async def disable_post_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    settings.post_time = ""
    save_settings(settings)
    _reschedule(context.application)
    await update.message.reply_text("Scheduled posting disabled.")


async def enable_llm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    settings.use_llm = True
    save_settings(settings)
    await update.message.reply_text("LLM summarization enabled.")


async def disable_llm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    settings.use_llm = False
    save_settings(settings)
    await update.message.reply_text("LLM summarization disabled.")


async def set_summarizer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    value = " ".join(context.args).strip().lower()
    if value not in {"auto", "openai", "ollama", "simple"}:
        await update.message.reply_text("Usage: /set_summarizer auto|openai|ollama|simple")
        return
    settings = load_settings()
    settings.summarizer_provider = value
    if value == "simple":
        settings.use_llm = False
    save_settings(settings)
    await update.message.reply_text(f"Summarizer set to: {value}")


async def _scheduled_post(app: Application) -> None:
    settings = load_settings()
    channel = settings.channel_id or os.getenv("PAPERS_DIGEST_CHANNEL_ID", "")
    if not channel:
        return
    try:
        digest = _build_digest(settings)
    except ValueError:
        return
    await app.bot.send_message(chat_id=channel, text=digest[:4096])


def _configure_scheduler(app: Application) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=_tzinfo())
    _apply_schedule(scheduler, app)
    scheduler.start()
    return scheduler


def _apply_schedule(scheduler: AsyncIOScheduler, app: Application) -> None:
    settings = load_settings()
    scheduler.remove_all_jobs()
    if not settings.post_time:
        return
    parsed = _parse_time(settings.post_time)
    if not parsed:
        return
    hour, minute = parsed
    scheduler.add_job(
        lambda: app.create_task(_scheduled_post(app)),
        "cron",
        hour=hour,
        minute=minute,
        id="daily_post",
        replace_existing=True,
    )


def _reschedule(app: Application) -> None:
    if _SCHEDULER is None:
        return
    _apply_schedule(_SCHEDULER, app)


def _tzinfo() -> ZoneInfo:
    tz = os.getenv("PAPERS_DIGEST_TIMEZONE", "UTC")
    try:
        return ZoneInfo(tz)
    except Exception:
        return ZoneInfo("UTC")


def main() -> None:
    token = os.getenv("PAPERS_DIGEST_BOT_TOKEN")
    if not token:
        raise RuntimeError("PAPERS_DIGEST_BOT_TOKEN is not set.")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_area", set_area))
    app.add_handler(CommandHandler("show_area", show_area))
    app.add_handler(CommandHandler("set_channel", set_channel))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("preview_today", preview_today))
    app.add_handler(CommandHandler("post_today", post_today))
    app.add_handler(CommandHandler("set_post_time", set_post_time))
    app.add_handler(CommandHandler("disable_post_time", disable_post_time))
    app.add_handler(CommandHandler("enable_llm", enable_llm))
    app.add_handler(CommandHandler("disable_llm", disable_llm))
    app.add_handler(CommandHandler("set_summarizer", set_summarizer))

    global _SCHEDULER
    _SCHEDULER = _configure_scheduler(app)
    app.run_polling()


if __name__ == "__main__":
    main()

