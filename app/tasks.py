from celery import Celery
from app.config import config
import time
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.news_parser.site_parser import SiteParser
from app.news_parser.tg_parser import TelegramParser
from app.utils.filters import NewsFilter
from app.openai_client import openai_client
from app.models import NewsItem, Post
from app.telegram.publisher_bot import PostPublisher

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
    """Тестовая задача для проверки Celery"""
    try:
        print("🐍 Celery worker работает!")
        return {"status": "success", "message": "Celery работает правильно"}
    except Exception as exc:
        print(f"❌ Ошибка test_task: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="slow_task", max_retries=3, default_retry_delay=60)
def slow_task(self, seconds: int = 5):
    """Задача с задержкой"""
    try:
        print(f"⏳ Начинаю задачу на {seconds} секунд...")
        time.sleep(seconds)
        print(f"✅ Задача выполнена через {seconds} секунд")
        return {"status": "done", "sleep_time": seconds}
    except Exception as exc:
        print(f"❌ Ошибка slow_task: {exc}")
        raise self.retry(exc=exc)


# ========== ОСНОВНЫЕ ЗАДАЧИ ==========

@celery_app.task(bind=True, name="parse_all_sources", max_retries=3, default_retry_delay=60)
def parse_all_sources(self):
    """Парсит все источники (сайты и TG каналы)"""
    try:
        db = SessionLocal()

        # Список источников
        sources = [
            {"type": "site", "name": "Habr", "url": "https://habr.com/ru/rss/all/all/?fl=ru"},
            {"type": "site", "name": "Postimees", "url": "https://rus.postimees.ee/rss"},
            # Telegram каналы временно отключены
            # {"type": "tg", "name": "Tech Morning", "username": "@tech_morning"},
            # {"type": "tg", "name": "Rus Delfie", "username": "@rusdelfiee"},
        ]

        all_news = []

        for source in sources:
            try:
                if source["type"] == "site":
                    parser = SiteParser(source["name"], source["url"])
                    news = parser.parse()
                else:
                    parser = TelegramParser(source["name"], source["username"])
                    news = parser.parse()

                all_news.extend(news)
                print(f"📰 {source['name']}: получено {len(news)} новостей")
            except Exception as e:
                print(f"❌ Ошибка парсинга {source['name']}: {e}")

        # Сохраняем новости в БД и фильтруем
        filter_obj = NewsFilter(db)
        saved_count = 0

        for news in all_news:
            content_hash = NewsItem.compute_hash(news['title'], news.get('summary', ''))
            existing = db.query(NewsItem).filter(NewsItem.content_hash == content_hash).first()

            if existing:
                print(f"⚠️ Дубль (хеш): {news['title'][:50]}")
                continue

            if filter_obj.filter_news(news):
                news_item = NewsItem(**news)
                news_item.content_hash = content_hash
                db.add(news_item)
                saved_count += 1

        db.commit()
        db.close()

        print(f"✅ Сохранено {saved_count} новостей после фильтрации")
        return {"parsed": len(all_news), "saved": saved_count}

    except Exception as exc:
        print(f"❌ Ошибка parse_all_sources: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="generate_post_for_news", max_retries=3, default_retry_delay=60)
def generate_post_for_news(self, news_id: str):
    """Генерирует пост для конкретной новости"""
    try:
        db = SessionLocal()

        news = db.query(NewsItem).filter(NewsItem.id == news_id).first()
        if not news:
            return {"error": "News not found"}

        existing_post = db.query(Post).filter(Post.news_id == news_id).first()
        if existing_post:
            return {"error": "Post already generated"}

        generated_text = openai_client.generate_post(news.raw_text or news.summary)

        post = Post(
            news_id=news_id,
            generated_text=generated_text,
            status="generated"
        )
        db.add(post)
        db.commit()
        db.close()

        return {"news_id": news_id, "post_id": post.id, "status": "generated"}

    except Exception as exc:
        print(f"❌ Ошибка generate_post_for_news: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="process_all_news", max_retries=3, default_retry_delay=60)
def process_all_news(self):
    """Обрабатывает все неподготовленные новости (парсинг → генерация)"""
    try:
        parse_result = parse_all_sources()

        db = SessionLocal()
        news_without_posts = db.query(NewsItem).outerjoin(
            Post, NewsItem.id == Post.news_id
        ).filter(Post.id == None).all()
        db.close()

        generated_count = 0
        for news in news_without_posts:
            generate_post_for_news.delay(news.id)
            generated_count += 1

        return {
            "parse_result": parse_result,
            "news_to_generate": generated_count,
            "status": "tasks_sent"
        }

    except Exception as exc:
        print(f"❌ Ошибка process_all_news: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="publish_post", max_retries=3, default_retry_delay=60)
def publish_post_task(self, post_id: str, channel: str = None):
    """Публикует конкретный пост"""
    try:
        db = SessionLocal()
        publisher = PostPublisher(db)
        success = publisher.publish_post(post_id, channel)
        db.close()
        return {"post_id": post_id, "success": success}

    except Exception as exc:
        print(f"❌ Ошибка publish_post_task: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="publish_all_pending", max_retries=3, default_retry_delay=60)
def publish_all_pending_task(self, channel: str = None):
    """Публикует все ожидающие посты"""
    try:
        db = SessionLocal()
        publisher = PostPublisher(db)
        result = publisher.publish_pending_posts(channel)
        db.close()
        return result

    except Exception as exc:
        print(f"❌ Ошибка publish_all_pending_task: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, name="full_news_cycle", max_retries=3, default_retry_delay=60)
def full_news_cycle(self):
    """Полный цикл: парсинг → генерация → публикация"""
    try:
        # Шаг 1: Парсинг
        parse_result = parse_all_sources()

        # Шаг 2: Генерация постов
        db = SessionLocal()
        news_without_posts = db.query(NewsItem).outerjoin(
            Post, NewsItem.id == Post.news_id
        ).filter(Post.id == None).all()
        db.close()

        generated_count = 0
        for news in news_without_posts:
            generate_post_for_news.delay(news.id)
            generated_count += 1

        # Шаг 3: Публикация с задержкой
        publish_all_pending_task.apply_async(args=[], countdown=10)

        return {
            "parse_result": parse_result,
            "generation_started": generated_count,
            "publication_scheduled": True
        }

    except Exception as exc:
        print(f"❌ Ошибка full_news_cycle: {exc}")
        raise self.retry(exc=exc)