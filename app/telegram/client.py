from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from app.config import config

_bot: Bot | None = None


def get_bot() -> Bot:
    """Синглтон aiogram Bot"""
    global _bot
    if _bot is None:
        _bot = Bot(
            token=config.TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    return _bot


async def close_bot() -> None:
    """Закрыть сессию бота"""
    global _bot
    if _bot is not None:
        await _bot.session.close()
    _bot = None