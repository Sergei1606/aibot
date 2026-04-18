from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    source = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # "site" или "tg"
    published_at = Column(DateTime, nullable=False)
    raw_text = Column(Text, nullable=True)
    is_filtered = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True, default=generate_uuid)
    news_id = Column(String, ForeignKey("news_items.id"), nullable=False)
    generated_text = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=True)
    status = Column(String, default="new")  # new/generated/published/failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)  # "site" или "tg"
    name = Column(String, nullable=False)
    url_or_username = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())