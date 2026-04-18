from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Схемы для источников
class SourceBase(BaseModel):
    type: str  # "site" или "tg"
    name: str
    url_or_username: str
    enabled: bool = True

class SourceCreate(SourceBase):
    pass

class SourceResponse(SourceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Схемы для ключевых слов
class KeywordBase(BaseModel):
    word: str

class KeywordCreate(KeywordBase):
    pass

class KeywordResponse(KeywordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Схемы для новостей
class NewsItemResponse(BaseModel):
    id: str
    title: str
    url: Optional[str]
    summary: str
    source: str
    source_type: str
    published_at: datetime
    is_filtered: bool

    class Config:
        from_attributes = True

# Схемы для постов
class PostResponse(BaseModel):
    id: str
    news_id: str
    generated_text: str
    published_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True

# Схема для ручной генерации
class GenerateRequest(BaseModel):
    news_text: str

class GenerateResponse(BaseModel):
    generated_text: str