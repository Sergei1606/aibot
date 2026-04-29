import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/aibot.db")

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Telegram API (для Telethon — парсинг каналов и публикация)
    TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # Канал для публикации
    DEFAULT_TELEGRAM_CHANNEL = os.getenv("DEFAULT_TELEGRAM_CHANNEL", "@your_channel")

    # Настройки парсинга
    PARSE_INTERVAL_MINUTES = 30

    # Фильтры (ключевые слова для включения)
    DEFAULT_KEYWORDS = ["новость", "технологии", "IT", "AI", "искусственный интеллект", "разработка"]

    # ID администратора для уведомлений об ошибках
    ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")


config = Config()