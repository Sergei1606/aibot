from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.tasks import generate_post_for_news, process_all_news, parse_all_sources
from app.openai_client import openai_client

router = APIRouter(prefix="/api", tags=["API"])

# ========== Эндпоинты для источников ==========
@router.get("/sources/", response_model=List[schemas.SourceResponse])
def get_sources(db: Session = Depends(get_db)):
    """Получить все источники"""
    sources = db.query(models.Source).all()
    return sources

@router.post("/sources/", response_model=schemas.SourceResponse)
def create_source(source: schemas.SourceCreate, db: Session = Depends(get_db)):
    """Добавить новый источник"""
    db_source = models.Source(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

@router.delete("/sources/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """Удалить источник"""
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return {"message": "Source deleted"}

# ========== Эндпоинты для ключевых слов ==========
@router.get("/keywords/", response_model=List[schemas.KeywordResponse])
def get_keywords(db: Session = Depends(get_db)):
    """Получить все ключевые слова"""
    keywords = db.query(models.Keyword).all()
    return keywords

@router.post("/keywords/", response_model=schemas.KeywordResponse)
def create_keyword(keyword: schemas.KeywordCreate, db: Session = Depends(get_db)):
    """Добавить ключевое слово"""
    db_keyword = models.Keyword(word=keyword.word)
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword

@router.delete("/keywords/{keyword_id}")
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """Удалить ключевое слово"""
    keyword = db.query(models.Keyword).filter(models.Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    db.delete(keyword)
    db.commit()
    return {"message": "Keyword deleted"}

# ========== Эндпоинты для новостей ==========
@router.get("/news/", response_model=List[schemas.NewsItemResponse])
def get_news(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Получить список новостей"""
    news = db.query(models.NewsItem).order_by(models.NewsItem.published_at.desc()).offset(skip).limit(limit).all()
    return news

@router.get("/news/{news_id}", response_model=schemas.NewsItemResponse)
def get_news_item(news_id: str, db: Session = Depends(get_db)):
    """Получить новость по ID"""
    news = db.query(models.NewsItem).filter(models.NewsItem.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news

# ========== Эндпоинты для постов ==========
@router.get("/posts/", response_model=List[schemas.PostResponse])
def get_posts(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Получить список постов"""
    posts = db.query(models.Post).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts

# ========== Эндпоинты для генерации ==========
@router.post("/generate/", response_model=schemas.GenerateResponse)
def generate_manual(request: schemas.GenerateRequest):
    """Ручная генерация поста из текста"""
    generated = openai_client.generate_post(request.news_text)
    return schemas.GenerateResponse(generated_text=generated)

@router.post("/generate-for-news/{news_id}")
def generate_for_news(news_id: str):
    """Запустить генерацию поста для конкретной новости"""
    task = generate_post_for_news.delay(news_id)
    return {"task_id": task.id, "status": "started"}

# ========== Эндпоинты для задач ==========
@router.post("/tasks/parse")
def start_parsing():
    """Запустить парсинг всех источников"""
    task = parse_all_sources.delay()
    return {"task_id": task.id, "status": "started"}

@router.post("/tasks/process-all")
def start_process_all():
    """Запустить полный цикл: парсинг → генерация постов"""
    task = process_all_news.delay()
    return {"task_id": task.id, "status": "started"}