from celery import Celery
from app.config import config
import time

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
            "schedule": 30 * 60,  # 30 минут в секундах
        },
        "publish-pending-5-min": {
            "task": "publish_all_pending",
            "schedule": 5 * 60,  # 5 минут
        },
    }
)

# Простая тестовая задача
@celery_app.task(name="test_task")
def test_task():
    """Тестовая задача для проверки Celery"""
    print("🐍 Celery worker работает!")
    return {"status": "success", "message": "Celery работает правильно"}

# Задача с задержкой (имитация работы)
@celery_app.task(name="slow_task")
def slow_task(seconds: int = 5):
    """Задача, которая выполняется несколько секунд"""
    print(f"⏳ Начинаю задачу на {seconds} секунд...")
    time.sleep(seconds)
    print(f"✅ Задача выполнена через {seconds} секунд")
    return {"status": "done", "sleep_time": seconds}


from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.news_parser.site_parser import SiteParser
from app.news_parser.tg_parser import TelegramParser
from app.utils.filters import NewsFilter
from app.openai_client import openai_client
from app.models import NewsItem, Post
from app.config import config


@celery_app.task(name="parse_all_sources")
def parse_all_sources():
    """Парсит все источники (сайты и TG каналы)"""
    db = SessionLocal()

    # Список источников (позже будем брать из БД)
    sources = [
        {"type": "site", "name": "Habr", "url": "https://habr.com/ru/rss/all/all/?fl=ru"},
        {"type": "site", "name": "Postimees", "url": "https://rus.postimees.ee/rss"},
        {"type": "tg", "name": "Tech Morning", "username": "@tech_morning"},
        {"type": "tg", "name": "Rus Delfie", "username": "@rusdelfiee"},
    ]

    all_news = []

    for source in sources:
        try:
            if source["type"] == "site":
                parser = SiteParser(source["name"], source["url"])
                news = parser.parse()
            else:  # tg
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
        # Вычисляем хеш для проверки дубля
        content_hash = NewsItem.compute_hash(news['title'], news.get('summary', ''))

        # Проверяем, есть ли уже такая новость
        existing = db.query(NewsItem).filter(NewsItem.content_hash == content_hash).first()
        if existing:
            print(f"⚠️ Дубль (хеш): {news['title'][:50]}")
            continue  # пропускаем дубль

        # Проверяем фильтрацию
        if filter_obj.filter_news(news):
            news_item = NewsItem(**news)
            news_item.content_hash = content_hash  # сохраняем хеш
            db.add(news_item)
            saved_count += 1

    db.commit()
    db.close()

    print(f"✅ Сохранено {saved_count} новостей после фильтрации")
    return {"parsed": len(all_news), "saved": saved_count}


@celery_app.task(name="generate_post_for_news")
def generate_post_for_news(news_id: str):
    """Генерирует пост для конкретной новости"""
    db = SessionLocal()

    try:
        news = db.query(NewsItem).filter(NewsItem.id == news_id).first()
        if not news:
            return {"error": "News not found"}

        # Проверяем, не сгенерирован ли уже пост
        existing_post = db.query(Post).filter(Post.news_id == news_id).first()
        if existing_post:
            return {"error": "Post already generated"}

        # Генерируем пост
        generated_text = openai_client.generate_post(news.raw_text or news.summary)

        # Сохраняем пост
        post = Post(
            news_id=news_id,
            generated_text=generated_text,
            status="generated"
        )
        db.add(post)
        db.commit()

        return {"news_id": news_id, "post_id": post.id, "status": "generated"}

    except Exception as e:
        print(f"Ошибка генерации поста: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="process_all_news")
def process_all_news():
    """Обрабатывает все неподготовленные новости (парсинг → генерация)"""
    # Сначала парсим источники
    parse_result = parse_all_sources()

    # Затем генерируем посты для новых новостей
    db = SessionLocal()

    # Находим новости без постов
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


from app.telegram.publisher import PostPublisher


@celery_app.task(name="publish_post")
def publish_post_task(post_id: str, channel: str = None):
    """Публикует конкретный пост"""
    db = SessionLocal()
    try:
        publisher = PostPublisher(db)
        success = publisher.publish_post(post_id, channel)
        return {"post_id": post_id, "success": success}
    finally:
        db.close()


@celery_app.task(name="publish_all_pending")
def publish_all_pending_task(channel: str = None):
    """Публикует все ожидающие посты"""
    db = SessionLocal()
    try:
        publisher = PostPublisher(db)
        result = publisher.publish_pending_posts(channel)
        return result
    finally:
        db.close()


@celery_app.task(name="full_news_cycle")
def full_news_cycle():
    """
    Полный цикл:
    1. Парсинг источников
    2. Генерация постов для новых новостей
    3. Публикация всех готовых постов
    """
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

    # Шаг 3: Публикация (отправляем отдельной задачей с задержкой)
    # Ждём 10 секунд, чтобы генерация успела выполниться
    publish_all_pending_task.apply_async(args=[], countdown=10)

    return {
        "parse_result": parse_result,
        "generation_started": generated_count,
        "publication_scheduled": True
    }