"""API-эндпоинты: CRUD источников, ключевых слов, запуск задач, статистика."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List
from app.database import get_db
from app import models, schemas
from app.tasks import generate_post_for_news, process_all_news, parse_all_sources
from app.ai.openai_client import openai_client

router = APIRouter(prefix="/api", tags=["API"])

# ========== Эндпоинты для источников ==========
@router.get("/sources/", response_model=List[schemas.SourceResponse])
async def get_sources(db: AsyncSession = Depends(get_db)):
    """Получить все источники"""
    result = await db.execute(select(models.Source))
    return list(result.scalars().all())

@router.post("/sources/", response_model=schemas.SourceResponse)
async def create_source(source: schemas.SourceCreate, db: AsyncSession = Depends(get_db)):
    """Добавить новый источник"""
    db_source = models.Source(**source.model_dump())
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    return db_source

@router.put("/sources/{source_id}", response_model=schemas.SourceResponse)
async def update_source(source_id: int, source_update: schemas.SourceCreate, db: AsyncSession = Depends(get_db)):
    """Обновить источник"""
    result = await db.execute(select(models.Source).filter(models.Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for key, value in source_update.model_dump().items():
        setattr(source, key, value)
    await db.commit()
    await db.refresh(source)
    return source

@router.delete("/sources/{source_id}")
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить источник"""
    result = await db.execute(select(models.Source).filter(models.Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(source)
    await db.commit()
    return {"message": "Source deleted"}

@router.get("/keywords/", response_model=List[schemas.KeywordResponse])
async def get_keywords(db: AsyncSession = Depends(get_db)):
    """Получить все ключевые слова"""
    result = await db.execute(select(models.Keyword))
    return list(result.scalars().all())

@router.post("/keywords/", response_model=schemas.KeywordResponse)
async def create_keyword(keyword: schemas.KeywordCreate, db: AsyncSession = Depends(get_db)):
    """Добавить ключевое слово"""
    db_keyword = models.Keyword(word=keyword.word)
    db.add(db_keyword)
    await db.commit()
    await db.refresh(db_keyword)
    return db_keyword

@router.put("/keywords/{keyword_id}", response_model=schemas.KeywordResponse)
async def update_keyword(keyword_id: int, keyword_update: schemas.KeywordCreate, db: AsyncSession = Depends(get_db)):
    """Обновить ключевое слово"""
    result = await db.execute(select(models.Keyword).filter(models.Keyword.id == keyword_id))
    keyword = result.scalar_one_or_none()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    for key, value in keyword_update.model_dump().items():
        setattr(keyword, key, value)
    await db.commit()
    await db.refresh(keyword)
    return keyword

@router.delete("/keywords/{keyword_id}")
async def delete_keyword(keyword_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить ключевое слово"""
    result = await db.execute(select(models.Keyword).filter(models.Keyword.id == keyword_id))
    keyword = result.scalar_one_or_none()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    await db.delete(keyword)
    await db.commit()
    return {"message": "Keyword deleted"}

@router.get("/news/", response_model=List[schemas.NewsItemResponse])
async def get_news(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Получить список новостей"""
    result = await db.execute(select(models.NewsItem).order_by(models.NewsItem.published_at.desc()).offset(skip).limit(limit))
    return list(result.scalars().all())

@router.get("/news/{news_id}", response_model=schemas.NewsItemResponse)
async def get_news_item(news_id: str, db: AsyncSession = Depends(get_db)):
    """Получить новость по ID"""
    result = await db.execute(select(models.NewsItem).filter(models.NewsItem.id == news_id))
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news

@router.get("/posts/", response_model=List[schemas.PostResponse])
async def get_posts(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Получить список постов"""
    result = await db.execute(select(models.Post).order_by(models.Post.created_at.desc()).offset(skip).limit(limit))
    return list(result.scalars().all())

@router.post("/generate/", response_model=schemas.GenerateResponse)
async def generate_manual(request: schemas.GenerateRequest):
    """Ручная генерация поста из текста"""
    generated = await openai_client.generate_post(request.news_text)
    return schemas.GenerateResponse(generated_text=generated)

@router.post("/generate-for-news/{news_id}")
async def generate_for_news(news_id: str):
    """Запустить генерацию поста для конкретной новости"""
    task = generate_post_for_news.delay(news_id)
    return {"task_id": task.id, "status": "started"}

@router.post("/tasks/parse")
async def start_parsing():
    """Запустить парсинг всех источников"""
    task = parse_all_sources.delay()
    return {"task_id": task.id, "status": "started"}

@router.post("/tasks/process-all")
async def start_process_all():
    """Запустить полный цикл: парсинг → генерация постов"""
    task = process_all_news.delay()
    return {"task_id": task.id, "status": "started"}

@router.get("/stats/")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Получить статистику"""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

    result = await db.execute(select(func.count(models.NewsItem.id)))
    total_news = result.scalar()

    result = await db.execute(
        select(func.count(models.Post.id)).filter(
            models.Post.status == "published",
            models.Post.published_at >= today
        )
    )
    published_today = result.scalar()

    result = await db.execute(
        select(func.count(models.Post.id)).filter(models.Post.status == "generated")
    )
    pending_posts = result.scalar()

    return {
        "total_news": total_news,
        "published_today": published_today,
        "pending_posts": pending_posts
    }


@router.get("/health")
async def health_check():
    """Проверка состояния API"""
    return {"status": "ok"}