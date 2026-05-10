"""Подключение к PostgreSQL: движок, сессии, создание таблиц."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.config import config
import os

# Создаём папку data, если её нет (для SQLite)
if "sqlite" in config.DATABASE_URL:
    os.makedirs("data", exist_ok=True)

engine = create_async_engine(
    config.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {},
    poolclass=NullPool
)

SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def init_db():
    """Создаёт все таблицы в базе данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ База данных инициализирована")

async def get_db():
    async with SessionLocal() as db:
        yield db