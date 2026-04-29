import feedparser
from datetime import datetime
from typing import List
from app.news_parser.base_parser import BaseParser
import aiohttp
import re
from app.logger import logger


class SiteParser(BaseParser):
    """Парсер RSS лент сайтов"""

    def __init__(self, source_name: str, rss_url: str):
        super().__init__(source_name, "site")
        self.rss_url = rss_url

    async def parse(self) -> List[dict]:
        """Парсит RSS и возвращает список новостей"""
        news_list = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.rss_url) as response:
                    content = await response.text()

            feed = feedparser.parse(content)

            for entry in feed.entries[:10]:  # Берём последние 10 записей
                # Получаем дату публикации
                published_at = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])

                # Получаем описание/суммари
                summary = entry.summary if hasattr(entry, 'summary') else entry.description if hasattr(entry,
                                                                                                       'description') else ""

                # Очищаем HTML теги из summary
                summary = re.sub(r'<[^>]+>', '', summary)[:500]

                news_item = self.create_news_item(
                    title=entry.title,
                    summary=summary,
                    url=entry.link,
                    published_at=published_at,
                    raw_text=summary
                )
                news_list.append(news_item)

        except Exception as e:
            logger.error(f"Ошибка парсинга сайта {self.source_name}: {e}")

        return news_list