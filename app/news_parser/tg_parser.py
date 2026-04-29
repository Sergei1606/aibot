from datetime import datetime
from typing import List, Optional
from telethon import TelegramClient
from app.news_parser.base_parser import BaseParser
from app.config import config
from app.logger import logger


class TelegramParser(BaseParser):
    """Парсер Telegram каналов через Telethon"""

    def __init__(self, source_name: str, channel_username: str):
        super().__init__(source_name, "tg")
        self.channel_username = channel_username
        self.client = None

    async def _get_client(self):
        """Создаёт клиент Telethon"""
        if self.client is None:
            self.client = TelegramClient(
                f"session_{self.source_name}",
                config.TELEGRAM_API_ID,
                config.TELEGRAM_API_HASH
            )
            await self.client.start()
        return self.client

    async def parse(self, limit: int = 10) -> List[dict]:
        """Асинхронный парсинг канала"""
        news_list = []

        try:
            client = await self._get_client()

            # Получаем последние сообщения из канала
            async for message in client.iter_messages(self.channel_username, limit=limit):
                if message.text and not message.text.startswith('/'):  # Пропускаем команды
                    news_item = self.create_news_item(
                        title=message.text[:100],  # Первые 100 символов как заголовок
                        summary=message.text[:500],
                        url=None,  # У сообщений TG нет URL
                        published_at=message.date.replace(tzinfo=None) if message.date else datetime.now(),
                        raw_text=message.text
                    )
                    news_list.append(news_item)

        except Exception as e:
            logger.error(f"Ошибка парсинга канала {self.source_name}: {e}")

        return news_list