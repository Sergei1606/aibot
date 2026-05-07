"""
Главный модуль FastAPI приложения AIBot.
Содержит инициализацию приложения, веб-интерфейс и управление жизненным циклом.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime
from app.database import engine, Base, get_db, SessionLocal
from app import models
from app.api import endpoints
from app.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup: создаём таблицы при запуске
    print("🚀 Starting application...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")

    # Заполняем ключевые слова и источники по умолчанию, если таблицы пусты
    async with SessionLocal() as db:
        # Ключевые слова
        result = await db.execute(select(models.Keyword))
        if not result.scalars().all():
            default_keywords = [
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
            for word in default_keywords:
                db.add(models.Keyword(word=word))
            await db.commit()
            logger.info(f"🔑 Добавлено {len(default_keywords)} ключевых слов по умолчанию")

        # Источники
        result = await db.execute(select(models.Source))
        if not result.scalars().all():
            default_sources = [
                models.Source(type="site", name="Habr", url="https://habr.com/ru/rss/all/all/?fl=ru"),
                models.Source(type="site", name="Postimees", url="https://rus.postimees.ee/rss"),
                models.Source(type="tg", name="Durov", tg_username="@durov"),
            ]
            db.add_all(default_sources)
            await db.commit()
            logger.info("📡 Источники добавлены по умолчанию")

    yield

    # Shutdown: закрываем соединения
    print("🛑 Shutting down application...")
    await engine.dispose()
    print("✅ Database connections closed")


app = FastAPI(
    title="AI News Bot for Telegram",
    version="1.0.0",
    lifespan=lifespan
)

# Подключаем роутеры
app.include_router(endpoints.router)

# Jinja2 для веб-интерфейса
templates = Jinja2Templates(directory="app/templates")


@app.get("/", include_in_schema=False)
async def root_ui(request: Request, db: AsyncSession = Depends(get_db)):
    # Получаем последние 10 постов
    result = await db.execute(
        select(models.Post).order_by(models.Post.created_at.desc()).limit(10)
    )
    posts = list(result.scalars().all())

    # Статистика
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
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
    return {"status": "healthy"}