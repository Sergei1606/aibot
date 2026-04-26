from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base
from app.api import endpoints


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup: создаём таблицы при запуске
    print("🚀 Starting application...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    yield
    # Shutdown: закрываем соединения (опционально)
    print("🛑 Shutting down application...")
    engine.dispose()
    print("✅ Database connections closed")


app = FastAPI(
    title="AI News Bot for Telegram",
    version="1.0.0",
    lifespan=lifespan
)

# Подключаем роутеры
app.include_router(endpoints.router)


@app.get("/")
def root():
    return {"message": "AI News Bot is running", "status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}