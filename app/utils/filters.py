"""Фильтрация новостей по ключевым словам и защита от дубликатов."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Keyword, NewsItem
from app.logger import logger


class NewsFilter:
    """Фильтрация новостей по ключевым словам и дублям"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_keywords(self) -> List[str]:
        """Получает список ключевых слов из БД"""
        result = await self.db.execute(select(Keyword))
        keywords = result.scalars().all()
        if not keywords:
            # Если нет ключевых слов в БД, используем дефолтные
            return ["новость", "технологии", "IT", "AI", "искусственный интеллект", "разработка", "python", "fastapi"]
        return [k.word.lower() for k in keywords]

    async def check_keywords(self, text: str) -> bool:
        """Проверяет, содержит ли текст ключевые слова"""
        if not text:
            return False

        text_lower = text.lower()
        keywords = await self.get_keywords()

        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        return False

    async def is_duplicate(self, title: str, source: str) -> bool:
        """Проверяет, не была ли такая новость уже добавлена"""
        result = await self.db.execute(
            select(NewsItem).filter(
                NewsItem.title == title,
                NewsItem.source == source
            )
        )
        existing = result.first()
        return existing is not None

    async def filter_news(self, news_item: dict) -> bool:
        """
        Фильтрует новость:
        - Проверяет по ключевым словам
        - Проверяет на дубликаты
        Возвращает True, если новость проходит фильтр
        """
        # Проверка на дубликат
        if await self.is_duplicate(news_item["title"], news_item["source"]):
            logger.warning(f"❌ Дубликат: {news_item['title'][:50]}")
            return False

        # Проверка ключевых слов
        text_to_check = f"{news_item['title']} {news_item['summary']}"
        if not await self.check_keywords(text_to_check):
            logger.info(f"❌ Нет ключевых слов: {news_item['title'][:50]}")
            return False

        logger.info(f"✅ Прошёл фильтр: {news_item['title'][:50]}")
        return True