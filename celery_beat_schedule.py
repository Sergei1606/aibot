from celery import Celery
from app.config import config

celery_app = Celery("aibot", broker=config.REDIS_URL)

celery_app.conf.update(
    timezone="Europe/Moscow",
    enable_utc=True,
    beat_schedule={
        # Полный цикл каждые 30 минут
        "full-news-cycle-30-min": {
            "task": "full_news_cycle",
            "schedule": 30 * 60,  # 30 минут
        },
        # Только парсинг каждые 15 минут (запасной вариант)
        "parse-only-15-min": {
            "task": "parse_all_sources",
            "schedule": 15 * 60,  # 15 минут
        },
        # Публикация ожидающих постов каждые 5 минут
        "publish-pending-5-min": {
            "task": "publish_all_pending",
            "schedule": 5 * 60,  # 5 минут
        },
    }
)