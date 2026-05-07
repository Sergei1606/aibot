# 🤖 AIBot — AI-генератор постов для Telegram

Автоматизированный конвейер: сбор новостей (RSS + Telegram) → фильтрация → AI-генерация (GPT) → публикация в Telegram-канал.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A?logo=celery)](https://docs.celeryq.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991?logo=openai&logoColor=white)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Возможности

| Функция | Описание |
|:---|:---|
| 📰 **Парсинг** | Автосбор новостей из RSS (Habr, Postimees) и Telegram-каналов (@durov) |
| 🔍 **Фильтрация** | Отбор по ключевым словам (68 слов) и защита от дубликатов (MD5) |
| 🤖 **AI-генерация** | Создание постов с emoji и call-to-action через OpenAI GPT-4 |
| 📤 **Публикация** | Отправка в Telegram-канал через aiogram с защитой от flood |
| ⏰ **Расписание** | Celery Beat: парсинг каждые 30 мин, публикация каждые 5 мин |
| 📡 **API** | Swagger UI — управление источниками, ключевыми словами, ручной запуск |
| 🖥 **Веб-интерфейс** | Статистика и последние посты на главной странице |
| 🐳 **Docker** | 5 контейнеров: web, worker, beat, redis, postgres |

---

## 🛠 Технологии

- **API:** FastAPI (асинхронный) + Swagger (/docs)
- **Очереди:** Celery + Redis (брокер и backend)
- **БД:** PostgreSQL 15 + SQLAlchemy 2.0 (asyncpg)
- **AI:** OpenAI API (GPT-4)
- **Парсинг:** feedparser (RSS) + Telethon (Telegram)
- **Публикация:** aiogram 3.x (Bot API)
- **Контейнеризация:** Docker Compose

---

## ⚙️ Быстрый старт

### 1. Клонировать и настроить .env

```powershell
git clone https://github.com/Sergei1606/aibot.git
cd aibot
```

Создать .env в корне:
```
TELEGRAM_BOT_TOKEN=123456:ABCdef
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef
TELEGRAM_PHONE_NUMBER=+79161234567
DATABASE_URL=postgresql+asyncpg://aibot:aibot@db:5432/aibotdb
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=sk-proj-...
DEFAULT_TELEGRAM_CHANNEL=@your_channel
```
### 2. Запустить
```
docker-compose up -d --build
```
### 3. Создать сессию Telethon (для @durov)
```
python -c "
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv
import os
load_dotenv()

async def main():
    client = TelegramClient('data/session_durov', 
        int(os.getenv('TELEGRAM_API_ID')), 
        os.getenv('TELEGRAM_API_HASH'))
    await client.start(phone=os.getenv('TELEGRAM_PHONE_NUMBER'))
    print('OK')
    await client.disconnect()
asyncio.run(main())
"
```
### 4. Открыть
- Swagger: http://localhost:8000/docs
- Веб-интерфейс: http://localhost:8000/

## 📡 API (основные эндпоинты)
- Метод	/	URL	/	Описание


- GET	/api/sources/	Источники
- POST	/api/sources/	Добавить источник
- GET	/api/keywords/	Ключевые слова
- POST	/api/keywords/	Добавить слово
- GET	/api/news/	Новости
- GET	/api/posts/	Посты
- POST	/api/generate/	Ручная генерация
- POST	/api/tasks/parse	Запуск парсинга
- POST	/api/tasks/process-all	Полный цикл
- GET	/api/stats/	Статистика
- GET	/health	Проверка

## ⏰ Расписание
- full_news_cycle — парсинг → генерация → публикация	- 30 мин
- publish_all_pending — публикация готовых постов	- 5 мин

## 📁 Структура
```
aibot/
├── app/
│   ├── api/             # CRUD-эндпоинты
│   ├── news_parser/     # RSS + Telegram парсеры
│   ├── telegram/        # aiogram publisher + client
│   ├── utils/           # фильтры
│   ├── templates/       # веб-интерфейс
│   ├── main.py          # FastAPI + lifespan
│   ├── tasks.py         # Celery задачи
│   ├── models.py        # SQLAlchemy модели
│   ├── config.py        # настройки
│   └── database.py      # подключение к БД
├── data/                # сессии Telethon
├── docker-compose.yml
└── requirements.txt
```
## 📝 Чек-лист
```
№	Функция	                        Статус
1	Сбор новостей (RSS)	         ✅
2	Сбор новостей (Telegram)	 ✅
3	Фильтрация по ключевым словам	 ✅
4	AI-генерация (OpenAI)	         ✅
5	Публикация в Telegram	         ✅
6	API (CRUD)	                 ✅
7	Документация (Swagger)	         ✅
8	Веб-интерфейс	                 ✅
9	Docker Compose	                 ✅
10	Celery Beat	                 ✅
```
Автор: Sergei Pavljuk
    Дата: 07.05.2026
