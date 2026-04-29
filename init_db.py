import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db

async def main():
    await init_db()
    print("✅ База данных инициализирована")

if __name__ == "__main__":
    asyncio.run(main())