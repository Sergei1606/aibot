import asyncio
import time
from app.logger import logger
from celery import Celery
from app.config import config
from sqlalchemy.future import select
from app.database import SessionLocal
from app.news_parser.site_parser import SiteParser
from app.news_parser.tg_parser import TelegramParser
from app.utils.filters import NewsFilter
from app.openai_client import openai_client
from app.models import NewsItem, Post
# === ЗАМЕНА: используем aiogram-публикатор ===
from app.telegram.publisher import publish_to_channel
from datetime import datetime

def run_async(coro):
    """Безопасный запуск асинхронной функции из синхронного Celery"""
    return asyncio.get_event_loop().run_until_complete(coro)

# Создаём Celery приложение
celery_app = Celery(
    "aibot",
    broker=config.REDIS_URL,
    backend=config.REDIS_URL
)

# Настройки Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    beat_schedule={
        "full-news-cycle-30-min": {
            "task": "full_news_cycle",
            "schedule": 30 * 60,
        },
        "publish-pending-5-min": {
            "task": "publish_all_pending",
            "schedule": 5 * 60,
        },
    }
)


# ========== ТЕСТОВЫЕ ЗАДАЧИ ==========
@celery_app.task(bind=True, name="test_task", max_retries=3, default_retry_delay=60)
def test_task(self):
    try:
        logger.info("🐍 Celery worker работает!")
        return {"status": "success", "message": "Celery работает правильно"}
    except Exception as exc:
        logger.error(f"❌ Ошибка test_task: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="slow_task", max_retries=3, default_retry_delay=60)
def slow_task(self, seconds: int = 5):
    try:
        logger.info(f"⏳ Начинаю задачу на {seconds} секунд...")
        time.sleep(seconds)
        logger.info(f"✅ Задача выполнена через {seconds} секунд")
        return {"status": "done", "sleep_time": seconds}
    except Exception as exc:
        logger.error(f"❌ Ошибка slow_task: {exc}")
        raise self.retry(exc=exc)


# ========== ОСНОВНЫЕ АСИНХРОННЫЕ ФУНКЦИИ ==========

async def async_parse_all_sources():
    async with SessionLocal() as db:
        sources = [
            {"type": "site", "name": "Habr", "url": "https://habr.com/ru/rss/all/all/?fl=ru"},
            {"type": "site", "name": "Postimees", "url": "https://rus.postimees.ee/rss"},
            {"type": "tg", "name": "Durov", "username": "@durov"},
        ]

        all_news = []

        for source in sources:
            try:
                if source["type"] == "site":
                    parser = SiteParser(source["name"], source["url"])
                    news = await parser.parse()
                else:
                    parser = TelegramParser(source["name"], source["username"])
                    news = await parser.parse()

                all_news.extend(news)
                logger.info(f"📰 {source['name']}: получено {len(news)} новостей")
            except Exception as e:
                logger.error(f"❌ Ошибка парсинга {source['name']}: {e}")

        # Сохраняем и фильтруем
        filter_obj = NewsFilter(db)
        saved_count = 0

        for news in all_news:
            content_hash = NewsItem.compute_hash(news['title'], news.get('summary', ''))
            result = await db.execute(select(NewsItem).filter(NewsItem.content_hash == content_hash))
            existing = result.first()

            if existing:
                logger.info(f"⚠️ Дубль (хеш): {news['title'][:50]}")
                continue

            if await filter_obj.filter_news(news):
                news_item = NewsItem(**news)
                news_item.content_hash = content_hash
                db.add(news_item)
                saved_count += 1

        await db.commit()

        logger.info(f"✅ Сохранено {saved_count} новостей после фильтрации")
        return {"parsed": len(all_news), "saved": saved_count}


async def async_generate_post_for_news(news_id: str):
    async with SessionLocal() as db:
        result = await db.execute(select(NewsItem).filter(NewsItem.id == news_id))
        news = result.scalar_one_or_none()
        if not news:
            return {"error": "News not found"}

        result = await db.execute(select(Post).filter(Post.news_id == news_id))
        existing_post = result.scalar_one_or_none()
        if existing_post:
            return {"error": "Post already generated"}

        generated_text = await openai_client.generate_post(news.raw_text or news.summary)

        post = Post(
            news_id=news_id,
            generated_text=generated_text,
            status="generated"
        )
        db.add(post)
        await db.commit()

        return {"news_id": news_id, "post_id": post.id, "status": "generated"}


async def async_process_all_news():
    parse_result = await async_parse_all_sources()

    async with SessionLocal() as db:
        result = await db.execute(
            select(NewsItem).outerjoin(Post, NewsItem.id == Post.news_id).filter(Post.id == None)
        )
        news_without_posts = result.scalars().all()

    generated_count = 0
    for news in news_without_posts:
        generate_post_for_news.delay(news.id)
        generated_count += 1

    return {
        "parse_result": parse_result,
        "news_to_generate": generated_count,
        "status": "tasks_sent"
    }


# === НОВАЯ РЕАЛИЗАЦИЯ ПУБЛИКАЦИИ (aiogram) ===
async def async_publish_post_task(post_id: str, channel: str = None):
    """Публикует один пост по ID"""
    async with SessionLocal() as db:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()

        if not post:
            return {"error": "Post not found"}
        if post.status == "published":
            return {"error": "Post already published"}

        # Вызываем aiogram-публикатор
        success = await publish_to_channel(post.generated_text, channel)

        if success:
            post.status = "published"
            post.published_at = datetime.now()
            await db.commit()
            logger.info(f"✅ Пост {post_id} опубликован")
        else:
            post.status = "failed"
            await db.commit()
            logger.error(f"❌ Пост {post_id} не опубликован")

        return {"post_id": post_id, "success": success}


async def async_publish_all_pending_task(channel: str = None):
    """Публикует все посты со статусом 'generated'"""
    async with SessionLocal() as db:
        result = await db.execute(select(Post).where(Post.status == "generated"))
        pending = result.scalars().all()

        published = 0
        failed = 0
        for post in pending:
            success = await publish_to_channel(post.generated_text, channel)
            if success:
                post.status = "published"
                post.published_at = datetime.now()
                published += 1
            else:
                post.status = "failed"
                failed += 1

            await db.commit()
            await asyncio.sleep(3)  # ← задержка 3 секунды между постами

        logger.info(f"📊 Публикация завершена: {published} успешно, {failed} ошибок")
        return {"published": published, "failed": failed, "total": len(pending)}


async def async_full_news_cycle():
    """Полный цикл: парсинг → генерация → публикация"""
    # Парсим и генерируем
    process_result = await async_process_all_news()

    # Планируем публикацию всех готовых постов через 10 секунд
    publish_all_pending_task.apply_async(args=[], countdown=10)

    return {
        "parse_result": process_result.get("parse_result"),
        "generation_started": process_result.get("news_to_generate"),
        "publication_scheduled": True
    }


# ========== CELERY ТАСКИ (обёртки) ==========
@celery_app.task(bind=True, name="parse_all_sources", max_retries=3, default_retry_delay=60)
def parse_all_sources(self):
    try:
        return run_async(async_parse_all_sources())
    except Exception as exc:
        logger.error(f"❌ Ошибка parse_all_sources: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="generate_post_for_news", max_retries=3, default_retry_delay=60)
def generate_post_for_news(self, news_id: str):
    try:
        return run_async(async_generate_post_for_news(news_id))
    except Exception as exc:
        logger.error(f"❌ Ошибка generate_post_for_news: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="process_all_news", max_retries=3, default_retry_delay=60)
def process_all_news(self):
    try:
        return run_async(async_process_all_news())
    except Exception as exc:
        logger.error(f"❌ Ошибка process_all_news: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="publish_post", max_retries=3, default_retry_delay=60)
def publish_post_task(self, post_id: str, channel: str = None):
    try:
        return run_async(async_publish_post_task(post_id, channel))
    except Exception as exc:
        logger.error(f"❌ Ошибка publish_post_task: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="publish_all_pending", max_retries=3, default_retry_delay=60)
def publish_all_pending_task(self, channel: str = None):
    try:
        return run_async(async_publish_all_pending_task(channel))
    except Exception as exc:
        logger.error(f"❌ Ошибка publish_all_pending_task: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="full_news_cycle", max_retries=3, default_retry_delay=60)
def full_news_cycle(self):
    try:
        return run_async(async_full_news_cycle())
    except Exception as exc:
        logger.error(f"❌ Ошибка full_news_cycle: {exc}")
        raise self.retry(exc=exc)