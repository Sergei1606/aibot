"""
Асинхронные задачи Celery для обработки новостей.
Управляет полным циклом: парсинг, генерация постов и их публикация.
"""
import asyncio
import time
from app.logger import logger
from celery import Celery
from app.config import config
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.news_parser.site_parser import SiteParser
from app.news_parser.tg_parser import TelegramParser
from app.utils.filters import NewsFilter
from app.ai.openai_client import openai_client
from app.models import NewsItem, Post
from app.telegram.publisher import publish_to_channel
from datetime import datetime

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

def _get_local_sessionmaker():
    """Создает локальный engine и sessionmaker для каждой таски Celery, чтобы избежать ошибки greenlet_spawn"""
    engine = create_async_engine(
        config.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {},
        poolclass=NullPool
    )
    return engine, async_sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

# ========== ТЕСТОВЫЕ ЗАДАЧИ ==========

@celery_app.task(bind=True, name="test_task", max_retries=3, default_retry_delay=60)
def test_task(self):
    """Тестовая задача для проверки Celery"""
    try:
        logger.info("🐍 Celery worker работает!")
        return {"status": "success", "message": "Celery работает правильно"}
    except Exception as exc:
        logger.error(f"❌ Ошибка test_task: {exc}")
        raise self.retry(exc=exc)

@celery_app.task(bind=True, name="slow_task", max_retries=3, default_retry_delay=60)
def slow_task(self, seconds: int = 5):
    """Задача с задержкой"""
    try:
        logger.info(f"⏳ Начинаю задачу на {seconds} секунд...")
        time.sleep(seconds)
        logger.info(f"✅ Задача выполнена через {seconds} секунд")
        return {"status": "done", "sleep_time": seconds}
    except Exception as exc:
        logger.error(f"❌ Ошибка slow_task: {exc}")
        raise self.retry(exc=exc)

# ========== ОСНОВНЫЕ ЗАДАЧИ (ASYNC FUNCTIONS) ==========

async def async_parse_all_sources():
    engine, SessionLocal = _get_local_sessionmaker()
    async with SessionLocal() as db:
        # Список источников
        sources = [
            {"type": "site", "name": "Habr", "url": "https://habr.com/ru/rss/all/all/?fl=ru"},
            {"type": "site", "name": "Postimees", "url": "https://rus.postimees.ee/rss"},
            # Telegram каналы раскомментированы для работы с Telethon
            {"type": "tg", "name": "Tech Morning", "username": "@tech_morning"},
            {"type": "tg", "name": "Rus Delfie", "username": "@rusdelfiee"},
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

        # Сохраняем новости в БД и фильтруем
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
    await engine.dispose()
    return {"parsed": len(all_news), "saved": saved_count}


async def async_generate_post_for_news(news_id: str):
    engine, SessionLocal = _get_local_sessionmaker()
    async with SessionLocal() as db:
        result = await db.execute(select(NewsItem).filter(NewsItem.id == news_id))
        news = result.scalar_one_or_none()
        if not news:
            await engine.dispose()
            return {"error": "News not found"}

        result = await db.execute(select(Post).filter(Post.news_id == news_id))
        existing_post = result.scalar_one_or_none()
        if existing_post:
            await engine.dispose()
            return {"error": "Post already generated"}

        generated_text = await openai_client.generate_post(news.raw_text or news.summary)

        if news.url:
            generated_text += f"\n\n🔗 Источник: {news.url}"

        post = Post(
            news_id=news_id,
            generated_text=generated_text,
            status="generated"
        )
        db.add(post)
        await db.commit()
        
        post_id = post.id
        
    await engine.dispose()
    return {"news_id": news_id, "post_id": post_id, "status": "generated"}


async def async_process_all_news():
    parse_result = await async_parse_all_sources()

    engine, SessionLocal = _get_local_sessionmaker()
    async with SessionLocal() as db:
        result = await db.execute(
            select(NewsItem).outerjoin(Post, NewsItem.id == Post.news_id).filter(Post.id == None)
        )
        news_without_posts = result.scalars().all()

    generated_count = 0
    for news in news_without_posts:
        generate_post_for_news.delay(news.id)
        generated_count += 1

    await engine.dispose()
    return {
        "parse_result": parse_result,
        "news_to_generate": generated_count,
        "status": "tasks_sent"
    }


async def async_publish_post_task(post_id: str, channel: str = None):
    engine, SessionLocal = _get_local_sessionmaker()
    success = False
    async with SessionLocal() as db:
        result = await db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()

        if not post:
            logger.error(f"❌ Пост {post_id} не найден")
        elif post.status == "published":
            logger.warning(f"⚠️ Пост {post_id} уже опубликован")
        else:
            success = await publish_to_channel(post.generated_text, channel)
            if success:
                post.status = "published"
                post.published_at = datetime.now()
                logger.info(f"✅ Пост {post_id} опубликован")
            else:
                post.status = "failed"
                logger.error(f"❌ Пост {post_id} не опубликован")
            await db.commit()
            
    await engine.dispose()
    return {"post_id": post_id, "success": success}


async def async_publish_all_pending_task(channel: str = None):
    engine, SessionLocal = _get_local_sessionmaker()
    published = 0
    failed = 0
    total = 0
    async with SessionLocal() as db:
        result = await db.execute(select(Post).where(Post.status == "generated"))
        pending = result.scalars().all()
        total = len(pending)

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

    await engine.dispose()
    return {"published": published, "failed": failed, "total": total}


async def async_full_news_cycle():
    parse_result = await async_parse_all_sources()

    engine, SessionLocal = _get_local_sessionmaker()
    async with SessionLocal() as db:
        result = await db.execute(
            select(NewsItem).outerjoin(Post, NewsItem.id == Post.news_id).filter(Post.id == None)
        )
        news_without_posts = result.scalars().all()

    generated_count = 0
    for news in news_without_posts:
        generate_post_for_news.delay(news.id)
        generated_count += 1

    publish_all_pending_task.apply_async(args=[], countdown=10)

    await engine.dispose()
    return {
        "parse_result": parse_result,
        "generation_started": generated_count,
        "publication_scheduled": True
    }


# ========== CELERY ТАСКИ ==========

@celery_app.task(bind=True, name="parse_all_sources", max_retries=3, default_retry_delay=60)
def parse_all_sources(self):
    """Парсит все источники (сайты и TG каналы)"""
    try:
        return asyncio.run(async_parse_all_sources())
    except Exception as exc:
        logger.error(f"❌ Ошибка parse_all_sources: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="generate_post_for_news", max_retries=3, default_retry_delay=60)
def generate_post_for_news(self, news_id: str):
    """Генерирует пост для конкретной новости"""
    try:
        return asyncio.run(async_generate_post_for_news(news_id))
    except Exception as exc:
        logger.error(f"❌ Ошибка generate_post_for_news: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="process_all_news", max_retries=3, default_retry_delay=60)
def process_all_news(self):
    """Обрабатывает все неподготовленные новости (парсинг → генерация)"""
    try:
        return asyncio.run(async_process_all_news())
    except Exception as exc:
        logger.error(f"❌ Ошибка process_all_news: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="publish_post", max_retries=3, default_retry_delay=60)
def publish_post_task(self, post_id: str, channel: str = None):
    """Публикует конкретный пост"""
    try:
        return asyncio.run(async_publish_post_task(post_id, channel))
    except Exception as exc:
        logger.error(f"❌ Ошибка publish_post_task: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="publish_all_pending", max_retries=3, default_retry_delay=60)
def publish_all_pending_task(self, channel: str = None):
    """Публикует все ожидающие посты"""
    try:
        return asyncio.run(async_publish_all_pending_task(channel))
    except Exception as exc:
        logger.error(f"❌ Ошибка publish_all_pending_task: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="full_news_cycle", max_retries=3, default_retry_delay=60)
def full_news_cycle(self):
    """Полный цикл: парсинг → генерация → публикация"""
    try:
        return asyncio.run(async_full_news_cycle())
    except Exception as exc:
        logger.error(f"❌ Ошибка full_news_cycle: {exc}")
        raise self.retry(exc=exc)