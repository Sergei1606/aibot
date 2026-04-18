import feedparser
from datetime import datetime
from typing import List
from app.news_parser.base_parser import BaseParser


class SiteParser(BaseParser):
    """Парсер RSS лент сайтов"""

    def __init__(self, source_name: str, rss_url: str):
        super().__init__(source_name, "site")
        self.rss_url = rss_url

    def parse(self) -> List[dict]:
        """Парсит RSS и возвращает список новостей"""
        news_list = []

        try:
            feed = feedparser.parse(self.rss_url)

            for entry in feed.entries[:10]:  # Берём последние 10 записей
                # Получаем дату публикации
                published_at = datetime.now()
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6])

                # Получаем описание/суммари
                summary = entry.summary if hasattr(entry, 'summary') else entry.description if hasattr(entry,
                                                                                                       'description') else ""

                # Очищаем HTML теги из summary
                import re
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
            print(f"Ошибка парсинга сайта {self.source_name}: {e}")

        return news_list