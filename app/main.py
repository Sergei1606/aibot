from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime
from app.database import engine, Base, get_db
from app import models
from app.api import endpoints


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup: создаём таблицы при запуске
    print("🚀 Starting application...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")
    yield
    # Shutdown: закрываем соединения (опционально)
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


templates = Jinja2Templates(directory="app/templates")

@app.get("/", include_in_schema=False)
async def root_ui(request: Request, db: AsyncSession = Depends(get_db)):
    # Получаем последние 10 постов
    result = await db.execute(select(models.Post).order_by(models.Post.created_at.desc()).limit(10))
    posts = list(result.scalars().all())
    
    # Получаем стату
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(select(func.count(models.Post.id)).filter(models.Post.status == "published", models.Post.published_at >= today))
    published_today = result.scalar() or 0
    
    result = await db.execute(select(func.count(models.Post.id)).filter(models.Post.status == "generated"))
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