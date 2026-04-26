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

# Экспортируем логгер
__all__ = ["logger"]