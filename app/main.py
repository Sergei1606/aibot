from fastapi import FastAPI
from app.database import engine, Base
from app.api import endpoints

# Создаём таблицы при запуске
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI News Bot for Telegram", version="1.0.0")

# Подключаем роутеры
app.include_router(endpoints.router)

@app.get("/")
def root():
    return {"message": "AI News Bot is running", "status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}