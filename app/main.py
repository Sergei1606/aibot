"""Точка входа FastAPI: инициализация БД, веб-интерфейс, health-check."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timezone
from app.database import engine, Base, get_db, SessionLocal
from app import models
from app.api import endpoints
from app.logger import logger

# Константы для автоинициализации
DEFAULT_KEYWORDS = [
    "AI", "ML", "GPT", "LLM", "OpenAI", "Copilot",
    "искусственный интеллект", "машинное обучение", "нейросет",
    "ChatGPT", "Claude", "Gemini", "DeepSeek", "Grok",
    "MCP", "AGI", "prompt", "промпт", "agent", "агент",
    "python", "fastapi", "docker", "github", "gitlab",
    "postgresql", "redis", "celery", "rabbitmq", "kafka",
    "linux", "bash", "devops", "backend", "frontend",
    "fullstack", "аутентификация", "авторизация",
    "Cursor", "Windsurf", "Bolt", "Replit", "Vercel",
    "VS Code", "PyCharm", "JetBrains",
    "стартап", "инвестиции", "MVP", "POC",
    "производительность", "оптимизация", "методологи",
    "agile", "scrum", "kanban",
    "telegram", "бот", "чат", "канал", "OSINT",
    "технологии", "разработка", "программирование",
    "open source", "API", "security", "кибербезопасность"
]

DEFAULT_SOURCES = [
    {"type": "site", "name": "Habr", "url": "https://habr.com/ru/rss/all/all/?fl=ru"},
    {"type": "site", "name": "Postimees", "url": "https://rus.postimees.ee/rss"},
    {"type": "tg", "name": "Durov", "tg_username": "@durov"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы базы данных созданы")

    async with SessionLocal() as db:
        result = await db.execute(select(models.Keyword))
        existing_keywords = {k.word for k in result.scalars().all()}
        added_kw_count = 0
        for word in DEFAULT_KEYWORDS:
            if word not in existing_keywords:
                db.add(models.Keyword(word=word))
                added_kw_count += 1
        if added_kw_count > 0:
            await db.commit()
            logger.info(f"Добавлено {added_kw_count} новых ключевых слов")

        result = await db.execute(select(models.Source))
        existing_source_names = {src.name for src in result.scalars().all()}
        added_src_count = 0
        for src in DEFAULT_SOURCES:
            if src["name"] not in existing_source_names:
                db.add(models.Source(**src))
                added_src_count += 1
        if added_src_count > 0:
            await db.commit()
            logger.info(f"Добавлено {added_src_count} новых источников")

    yield

    await engine.dispose()
    logger.info("Приложение остановлено")


app = FastAPI(
    title="AI News Bot for Telegram",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(endpoints.router)

templates = Jinja2Templates(directory="app/templates")


@app.get("/", include_in_schema=False)
async def root_ui(request: Request, db: AsyncSession = Depends(get_db)):
    """Веб-интерфейс: статистика и последние посты."""
    result = await db.execute(
        select(models.Post).order_by(models.Post.created_at.desc()).limit(10)
    )
    posts = list(result.scalars().all())

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    result = await db.execute(
        select(func.count(models.Post.id)).filter(
            models.Post.status == "published",
            models.Post.published_at >= today
        )
    )
    published_today = result.scalar() or 0

    result = await db.execute(
        select(func.count(models.Post.id)).filter(models.Post.status == "generated")
    )
    pending_posts = result.scalar() or 0

    return templates.TemplateResponse("index.html", {
        "request": request,
        "posts": posts,
        "published_today": published_today,
        "pending_posts": pending_posts
    })


@app.get("/health")
async def health_check():
    """Health-check эндпоинт."""
    return {"status": "healthy"}


@app.get("/admin", include_in_schema=False)
async def admin_ui(request: Request):
    """Веб-интерфейс: панель администратора."""
    return templates.TemplateResponse("admin.html", {"request": request})