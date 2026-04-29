from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import config

engine = create_async_engine(
    config.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {}
)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as db:
        yield db