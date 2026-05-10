"""Настройка логирования через loguru."""

from loguru import logger
import sys

# Настройка логирования
logger.remove()  # Удаляем стандартный обработчик

# Добавляем вывод в консоль с цветом
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Добавляем запись в файл (опционально)
logger.add(
    "logs/aibot.log",
    rotation="1 day",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
    level="DEBUG"
)

# Синхронный sink для отправки критических ошибок в Telegram
import urllib.request
import json
from app.config import config

def telegram_sink(message):
    record = message.record
    if record["level"].name in ["ERROR", "CRITICAL"] and config.ADMIN_TELEGRAM_ID and config.TELEGRAM_BOT_TOKEN:
        try:
            text = f"🚨 <b>ERROR in AIBot</b>\n\n<b>Source:</b> {record['name']}:{record['function']}\n<b>Message:</b> {record['message']}"
            url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
            data = json.dumps({"chat_id": config.ADMIN_TELEGRAM_ID, "text": text, "parse_mode": "HTML"}).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

logger.add(telegram_sink, level="ERROR")

# Экспортируем логгер
__all__ = ["logger"]