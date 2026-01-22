from __future__ import annotations

import os
from datetime import date
from typing import Iterable

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from papers_digest.pipeline import run_digest
from papers_digest.settings import load_settings, save_settings, Settings


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
        "/preview_today, /post_today"
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
    await update.message.reply_text(f"Science area: {area}\nChannel: {channel}")


def _build_digest(settings: Settings) -> str:
    query = settings.science_area.strip()
    if not query:
        raise ValueError("Science area is not set. Use /set_area.")
    return run_digest(query=query, target_date=date.today(), limit=8)


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

    app.run_polling()


if __name__ == "__main__":
    main()

