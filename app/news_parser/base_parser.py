"""Базовый класс парсера новостей."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional


class BaseParser(ABC):
    """Базовый класс для всех парсеров"""

    def __init__(self, source_name: str, source_type: str):
        self.source_name = source_name
        self.source_type = source_type

    @abstractmethod
    async def parse(self) -> List[dict]:
        """Парсит источник и возвращает список словарей с данными новостей"""
        pass

    def create_news_item(self, title: str, summary: str, url: Optional[str],
                         published_at: datetime, raw_text: Optional[str] = None) -> dict:
        """Создаёт словарь новости для сохранения в БД"""
        return {
            "title": title,
            "summary": summary,
            "url": url,
            "source": self.source_name,
            "source_type": self.source_type,
            "published_at": published_at,
            "raw_text": raw_text or summary,
            "is_filtered": False
        }