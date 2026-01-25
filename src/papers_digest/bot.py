from __future__ import annotations

import logging
import os
from datetime import date
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.constants import ChatType
from telegram.error import NetworkError, TelegramError, TimedOut
from telegram.ext import Application, CommandHandler, ContextTypes

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from papers_digest.pipeline import run_digest
from papers_digest.settings import (
    Settings,
    ChannelConfig,
    load_settings,
    save_settings,
    get_channel_config,
    add_channel,
    remove_channel,
)
from papers_digest.summarizer import OllamaSummarizer, OpenAISummarizer, SimpleSummarizer, Summarizer

logger = logging.getLogger(__name__)
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
        await update.message.reply_text("Доступ запрещен. Свяжитесь с администратором.")
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    await update.message.reply_text(
        "Панель администратора готова.\n\n"
        "Управление каналами:\n"
        "/channels - список каналов\n"
        "/add_channel <@channel> <область> - добавить канал\n"
        "/remove_channel <@channel> - удалить канал\n"
        "/channel_info <@channel> - информация о канале\n"
        "/channel_set_area <@channel> <область> - установить область\n"
        "/channel_set_time <@channel> <ЧЧ:ММ> - установить время\n"
        "\nДругие команды:\n"
        "/preview_today [@channel] - предпросмотр\n"
        "/post_today [@channel] - опубликовать\n"
        "/status - общий статус"
    )


async def set_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Использование: /set_area <область науки>")
        return
    settings = load_settings()
    settings.science_area = text
    save_settings(settings)
    await update.message.reply_text(f"Область науки установлена: {text}")


async def show_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    area = settings.science_area or "Не установлена"
    await update.message.reply_text(f"Область науки: {area}")


async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Legacy command for backward compatibility."""
    if not await _require_admin(update):
        return
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Использование: /set_channel <channel_id или @channel>\n(Рекомендуется использовать /add_channel)")
        return
    settings = load_settings()
    # Add as new channel or update legacy channel_id
    config = add_channel(settings, text, settings.science_area)
    settings.channel_id = text  # Keep for legacy
    save_settings(settings)
    await update.message.reply_text(f"Канал установлен: {text}\n(Рекомендуется использовать /add_channel для управления несколькими каналами)")


async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    if not settings.channels:
        await update.message.reply_text("Каналы не настроены. Используйте /add_channel для добавления.")
        return
    lines = ["Настроенные каналы:\n"]
    for channel_id, config in settings.channels.items():
        status = "✓" if config.enabled else "✗"
        area = config.science_area or "не установлена"
        time = config.post_time or "не установлено"
        lines.append(f"{status} {channel_id}")
        lines.append(f"   Область: {area}")
        lines.append(f"   Время: {time}\n")
    await update.message.reply_text("\n".join(lines))


async def add_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    args = context.args or []
    if len(args) < 1:
        await update.message.reply_text("Использование: /add_channel <@channel> [область науки]")
        return
    channel_id = args[0].strip()
    science_area = " ".join(args[1:]).strip() if len(args) > 1 else ""
    settings = load_settings()
    config = add_channel(settings, channel_id, science_area)
    save_settings(settings)
    msg = f"Канал {channel_id} добавлен."
    if science_area:
        msg += f"\nОбласть науки: {science_area}"
    await update.message.reply_text(msg)


async def remove_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    channel_id = " ".join(context.args).strip() if context.args else ""
    if not channel_id:
        await update.message.reply_text("Использование: /remove_channel <@channel>")
        return
    settings = load_settings()
    if remove_channel(settings, channel_id):
        save_settings(settings)
        await update.message.reply_text(f"Канал {channel_id} удален.")
    else:
        await update.message.reply_text(f"Канал {channel_id} не найден.")


async def channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    channel_id = " ".join(context.args).strip() if context.args else ""
    if not channel_id:
        await update.message.reply_text("Использование: /channel_info <@channel>")
        return
    settings = load_settings()
    config = get_channel_config(settings, channel_id)
    if not config:
        await update.message.reply_text(f"Канал {channel_id} не найден.")
        return
    llm_status = "включен" if config.use_llm else "выключен"
    status = "включен" if config.enabled else "выключен"
    await update.message.reply_text(
        f"Канал: {config.channel_id}\n"
        f"Область науки: {config.science_area or 'не установлена'}\n"
        f"Время публикации: {config.post_time or 'не установлено'}\n"
        f"LLM: {llm_status}\n"
        f"Саммаризатор: {config.summarizer_provider}\n"
        f"Статус: {status}"
    )


async def channel_set_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Использование: /channel_set_area <@channel> <область науки>")
        return
    channel_id = args[0].strip()
    area = " ".join(args[1:]).strip()
    settings = load_settings()
    config = get_channel_config(settings, channel_id)
    if not config:
        await update.message.reply_text(f"Канал {channel_id} не найден. Используйте /add_channel для добавления.")
        return
    config.science_area = area
    save_settings(settings)
    await update.message.reply_text(f"Область науки для {channel_id} установлена: {area}")


async def channel_set_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Использование: /channel_set_time <@channel> <ЧЧ:ММ>")
        return
    channel_id = args[0].strip()
    time_str = args[1].strip()
    parsed = _parse_time(time_str)
    if not parsed:
        await update.message.reply_text("Неверный формат времени. Используйте ЧЧ:ММ (24ч)")
        return
    settings = load_settings()
    config = get_channel_config(settings, channel_id)
    if not config:
        await update.message.reply_text(f"Канал {channel_id} не найден. Используйте /add_channel для добавления.")
        return
    config.post_time = time_str
    save_settings(settings)
    _reschedule(context.application)
    await update.message.reply_text(f"Время публикации для {channel_id} установлено: {time_str}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    area = settings.science_area or "Не установлена"
    channel = settings.channel_id or os.getenv("PAPERS_DIGEST_CHANNEL_ID", "") or "Не установлен"
    post_time = settings.post_time or "Не установлено"
    llm_enabled = "включен" if settings.use_llm else "выключен"
    summarizer = settings.summarizer_provider
    await update.message.reply_text(
        f"Область науки: {area}\nКанал: {channel}\nВремя публикации: {post_time}\n"
        f"LLM: {llm_enabled}\nСаммаризатор: {summarizer}"
    )

def _pick_summarizer(config: ChannelConfig | Settings) -> Summarizer:
    """Pick summarizer based on channel config or global settings."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    use_llm = config.use_llm if isinstance(config, ChannelConfig) else config.use_llm
    provider = config.summarizer_provider if isinstance(config, ChannelConfig) else (config.summarizer_provider or "auto")
    
    if use_llm and provider == "openai" and api_key:
        return OpenAISummarizer(api_key)
    if use_llm and provider == "ollama":
        return OllamaSummarizer()
    if use_llm and provider == "auto":
        if api_key:
            return OpenAISummarizer(api_key)
        return OllamaSummarizer()
    return SimpleSummarizer()


def _build_digest(config: ChannelConfig) -> list[str]:
    """Build digest for a specific channel configuration."""
    query = config.science_area.strip()
    if not query:
        raise ValueError(f"Область науки не установлена для канала {config.channel_id}. Используйте /channel_set_area.")
    return run_digest(query=query, target_date=date.today(), limit=8, summarizer=_pick_summarizer(config))


async def _safe_send_message(
    bot, chat_id: str | int, text: str, parse_mode: str | None = "MarkdownV2", max_retries: int = 3
) -> bool:
    """Safely send a message with retry logic."""
    # Ensure text doesn't exceed Telegram limit
    if len(text) > 4096:
        text = text[:4093] + "..."
    
    for attempt in range(max_retries):
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
            return True
        except (TimedOut, NetworkError) as e:
            logger.warning(f"Network error sending message (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to send message after {max_retries} attempts")
                return False
        except TelegramError as e:
            logger.error(f"Telegram error sending message: {e}")
            # Try without parse_mode if MarkdownV2 fails
            if parse_mode == "MarkdownV2" and attempt == 0:
                try:
                    await bot.send_message(chat_id=chat_id, text=text, parse_mode=None)
                    return True
                except Exception:
                    pass
            return False
    return False


async def _send_multiple_messages(bot, chat_id: str | int, messages: list[str]) -> bool:
    """Send multiple messages sequentially."""
    success = True
    for msg in messages:
        if not await _safe_send_message(bot, chat_id, msg):
            success = False
            # Small delay between messages to avoid rate limiting
            import asyncio
            await asyncio.sleep(0.5)
    return success


async def preview_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    # Check if channel specified
    channel_id = context.args[0].strip() if context.args else None
    if channel_id:
        config = get_channel_config(settings, channel_id)
        if not config:
            await _safe_send_message(context.bot, update.effective_chat.id, f"Канал {channel_id} не найден.", parse_mode=None)
            return
    else:
        # Use first channel or legacy settings
        if settings.channels:
            config = next(iter(settings.channels.values()))
        else:
            # Legacy: create temporary config from old settings
            from papers_digest.settings import ChannelConfig
            config = ChannelConfig(
                channel_id=settings.channel_id or "default",
                science_area=settings.science_area,
                use_llm=settings.use_llm,
                summarizer_provider=settings.summarizer_provider,
            )
    
    try:
        digest_parts = _build_digest(config)
    except ValueError as exc:
        await _safe_send_message(context.bot, update.effective_chat.id, str(exc), parse_mode=None)
        return
    except Exception as e:
        logger.error(f"Failed to build digest: {e}", exc_info=True)
        await _safe_send_message(
            context.bot, update.effective_chat.id, f"Ошибка генерации дайджеста: {e}. Некоторые источники могут быть недоступны.", parse_mode=None
        )
        return
    success = await _send_multiple_messages(context.bot, update.effective_chat.id, digest_parts)
    if not success:
        await _safe_send_message(context.bot, update.effective_chat.id, "Дайджест сгенерирован, но не удалось отправить некоторые части. Проверьте логи.", parse_mode=None)


async def post_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    # Check if channel specified
    channel_id = context.args[0].strip() if context.args else None
    if channel_id:
        config = get_channel_config(settings, channel_id)
        if not config:
            await _safe_send_message(context.bot, update.effective_chat.id, f"Канал {channel_id} не найден.", parse_mode=None)
            return
    else:
        # Use first channel or legacy settings
        if settings.channels:
            config = next(iter(settings.channels.values()))
            channel_id = config.channel_id
        else:
            # Legacy: use old channel_id
            channel_id = settings.channel_id or os.getenv("PAPERS_DIGEST_CHANNEL_ID", "")
            if not channel_id:
                await _safe_send_message(context.bot, update.effective_chat.id, "Канал не установлен. Используйте /add_channel или /post_today <@channel>.", parse_mode=None)
                return
            from papers_digest.settings import ChannelConfig
            config = ChannelConfig(
                channel_id=channel_id,
                science_area=settings.science_area,
                use_llm=settings.use_llm,
                summarizer_provider=settings.summarizer_provider,
            )
    
    try:
        digest_parts = _build_digest(config)
    except ValueError as exc:
        await _safe_send_message(context.bot, update.effective_chat.id, str(exc), parse_mode=None)
        return
    except Exception as e:
        logger.error(f"Failed to build digest: {e}", exc_info=True)
        await _safe_send_message(
            context.bot, update.effective_chat.id, f"Ошибка генерации дайджеста: {e}. Некоторые источники могут быть недоступны.", parse_mode=None
        )
        return
    success = await _send_multiple_messages(context.bot, channel_id, digest_parts)
    if success:
        await _safe_send_message(context.bot, update.effective_chat.id, f"Опубликовано в канале {channel_id}.", parse_mode=None)
    else:
        await _safe_send_message(context.bot, update.effective_chat.id, f"Не удалось опубликовать в канале {channel_id}. Проверьте логи.", parse_mode=None)


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
        await update.message.reply_text("Использование: /set_post_time ЧЧ:ММ (24ч)")
        return
    settings = load_settings()
    settings.post_time = value
    save_settings(settings)
    _reschedule(context.application)
    await update.message.reply_text(f"Время публикации установлено: {value}")


async def disable_post_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    settings.post_time = ""
    save_settings(settings)
    _reschedule(context.application)
    await update.message.reply_text("Автоматическая публикация отключена.")


async def enable_llm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    settings.use_llm = True
    save_settings(settings)
    await update.message.reply_text("LLM саммаризация включена.")


async def disable_llm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    settings = load_settings()
    settings.use_llm = False
    save_settings(settings)
    await update.message.reply_text("LLM саммаризация выключена.")


async def set_summarizer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update):
        return
    value = " ".join(context.args).strip().lower()
    if value not in {"auto", "openai", "ollama", "simple"}:
        await update.message.reply_text("Использование: /set_summarizer auto|openai|ollama|simple")
        return
    settings = load_settings()
    settings.summarizer_provider = value
    if value == "simple":
        settings.use_llm = False
    save_settings(settings)
    await update.message.reply_text(f"Саммаризатор установлен: {value}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the bot."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            error_msg = "Произошла ошибка. Попробуйте позже."
            if isinstance(context.error, (TimedOut, NetworkError)):
                error_msg = "Таймаут сети. Попробуйте еще раз."
            await _safe_send_message(context.bot, update.effective_chat.id, error_msg, parse_mode=None)
        except Exception:
            logger.error("Failed to send error message to user")


async def _scheduled_post(app: Application, channel_id: str) -> None:
    """Post digest to a specific channel."""
    settings = load_settings()
    config = get_channel_config(settings, channel_id)
    if not config or not config.enabled:
        return
    if not config.post_time:
        return
    try:
        digest_parts = _build_digest(config)
    except ValueError:
        logger.warning(f"Scheduled post skipped for {channel_id}: science area not set")
        return
    except Exception as e:
        logger.error(f"Scheduled post failed for {channel_id}: {e}", exc_info=True)
        return
    success = await _send_multiple_messages(app.bot, channel_id, digest_parts)
    if not success:
        logger.error(f"Failed to send scheduled post to channel {channel_id}")


def _configure_scheduler(app: Application) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=_tzinfo())
    _apply_schedule(scheduler, app)
    return scheduler


async def _post_init(app: Application) -> None:
    """Initialize scheduler after event loop is running."""
    global _SCHEDULER
    if _SCHEDULER is not None:
        _SCHEDULER.start()


def _apply_schedule(scheduler: AsyncIOScheduler, app: Application) -> None:
    """Apply schedule for all channels."""
    settings = load_settings()
    scheduler.remove_all_jobs()
    
    # Schedule posts for each channel
    for channel_id, config in settings.channels.items():
        if not config.enabled or not config.post_time:
            continue
        parsed = _parse_time(config.post_time)
        if not parsed:
            continue
        hour, minute = parsed
        scheduler.add_job(
            _scheduled_post,
            "cron",
            args=[app, channel_id],
            hour=hour,
            minute=minute,
            id=f"daily_post_{channel_id}",
            replace_existing=True,
        )
    
    # Legacy: support old single channel format
    if not settings.channels and settings.post_time:
        parsed = _parse_time(settings.post_time)
        if parsed:
            hour, minute = parsed
            channel_id = settings.channel_id or os.getenv("PAPERS_DIGEST_CHANNEL_ID", "")
            if channel_id:
                scheduler.add_job(
                    _scheduled_post,
                    "cron",
                    args=[app, channel_id],
                    hour=hour,
                    minute=minute,
                    id="daily_post_legacy",
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
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    token = os.getenv("PAPERS_DIGEST_BOT_TOKEN")
    if not token:
        raise RuntimeError("PAPERS_DIGEST_BOT_TOKEN is not set.")

    app = Application.builder().token(token).post_init(_post_init).build()
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    # Channel management
    app.add_handler(CommandHandler("channels", list_channels))
    app.add_handler(CommandHandler("add_channel", add_channel_cmd))
    app.add_handler(CommandHandler("remove_channel", remove_channel_cmd))
    app.add_handler(CommandHandler("channel_info", channel_info))
    app.add_handler(CommandHandler("channel_set_area", channel_set_area))
    app.add_handler(CommandHandler("channel_set_time", channel_set_time))
    # Legacy commands (kept for backward compatibility)
    app.add_handler(CommandHandler("set_area", set_area))
    app.add_handler(CommandHandler("show_area", show_area))
    app.add_handler(CommandHandler("set_channel", set_channel))
    # Other commands
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

