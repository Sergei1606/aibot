"""Публикация постов в Telegram-канал через aiogram."""

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from app.telegram.client import get_bot
from app.config import config
from app.logger import logger


async def publish_to_channel(text: str, channel: str = None) -> bool:
    """Публикует текст в Telegram-канал. Возвращает True при успехе."""
    target = channel or config.DEFAULT_TELEGRAM_CHANNEL

    if not target:
        logger.error("Telegram-канал не задан")
        return False
    if not text or not text.strip():
        logger.error("Текст поста пуст")
        return False

    bot = get_bot()

    try:
        logger.info(f"Публикация в {target}: {text[:60]}...")
        message = await bot.send_message(chat_id=target, text=text)
        logger.info(f"✅ Опубликовано. ID сообщения: {message.message_id}")
        return True
    except TelegramForbiddenError:
        logger.error(f"Нет прав для записи в канал {target}")
        return False
    except TelegramRetryAfter as e:
        logger.error(f"Rate limit, подождать {e.retry_after} сек")
        return False
    except TelegramBadRequest as e:
        logger.error(f"Ошибка запроса: {e}")
        return False
    except Exception as e:
        logger.error(f"Ошибка публикации: {e}")
        return False