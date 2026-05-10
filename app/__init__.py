"""Пакет приложения AIBot — AI-генератор постов для Telegram.

Основные модули:
- ai: интеграция с OpenAI API
- api: CRUD-эндпоинты FastAPI
- news_parser: парсеры RSS-лент и Telegram-каналов
- telegram: публикация постов через aiogram
- utils: фильтры, конфигурация, БД, Celery-задачи
"""