import re
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Keyword, NewsItem


class NewsFilter:
    """Фильтрация новостей по ключевым словам и дублям"""

    def __init__(self, db: Session):
        self.db = db

    def get_keywords(self) -> List[str]:
        """Получает список ключевых слов из БД"""
        keywords = self.db.query(Keyword).all()
        if not keywords:
            # Если нет ключевых слов в БД, используем дефолтные
            return ["новость", "технологии", "IT", "AI", "искусственный интеллект", "разработка", "python", "fastapi"]
        return [k.word.lower() for k in keywords]

    def check_keywords(self, text: str) -> bool:
        """Проверяет, содержит ли текст ключевые слова"""
        if not text:
            return False

        text_lower = text.lower()
        keywords = self.get_keywords()

        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        return False

    def is_duplicate(self, title: str, source: str) -> bool:
        """Проверяет, не была ли такая новость уже добавлена"""
        existing = self.db.query(NewsItem).filter(
            NewsItem.title == title,
            NewsItem.source == source
        ).first()
        return existing is not None

    def filter_news(self, news_item: dict) -> bool:
        """
        Фильтрует новость:
        - Проверяет по ключевым словам
        - Проверяет на дубликаты
        Возвращает True, если новость проходит фильтр
        """
        # Проверка на дубликат
        if self.is_duplicate(news_item["title"], news_item["source"]):
            print(f"❌ Дубликат: {news_item['title'][:50]}")
            return False

        # Проверка ключевых слов
        text_to_check = f"{news_item['title']} {news_item['summary']}"
        if not self.check_keywords(text_to_check):
            print(f"❌ Нет ключевых слов: {news_item['title'][:50]}")
            return False

        print(f"✅ Прошёл фильтр: {news_item['title'][:50]}")
        return True