# 🤖 AIBot — AI-генератор постов для Telegram

Мощный автоматизированный конвейер для сбора новостей из различных источников (RSS-ленты и Telegram-каналы), их фильтрации, рерайтинга с помощью ИИ (OpenAI GPT-4) и автоматической публикации готовых постов в Telegram-канал. 

Проект разработан в рамках модуля "Project M4: AI-генератор постов для Telegram".

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A?logo=celery)](https://docs.celeryq.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991?logo=openai&logoColor=white)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Возможности и Функционал

| Функция | Описание |
|:---|:---|
| 📰 **Агрегация контента** | Автосбор новостей из RSS (Habr, Postimees) и Telegram-каналов (например, @durov) через `Telethon`. |
| 🔍 **Умная фильтрация** | Отбор новостей по заданным ключевым словам (гибкая настройка через API) и защита от дубликатов (сравнение по MD5/контенту). |
| 🤖 **AI-генерация** | Создание лаконичных, вовлекающих постов с emoji и call-to-action через OpenAI GPT-4. |
| 📤 **Авто-публикация** | Отправка сгенерированных постов в целевой Telegram-канал через `aiogram` с защитой от флуда. |
| ⏰ **Асинхронные задачи и расписание** | Фоновая обработка через `Celery` и `Redis`. Запуск сбора каждые 30 мин, публикация готовых — каждые 5 мин. |
| 📡 **REST API & Swagger UI** | Полноценная панель управления (CRUD источников, ключевых слов, запуск задач, просмотр логов и постов). |
| 🖥 **Веб-интерфейс** | Визуализация статистики и просмотр последних опубликованных постов прямо в браузере. |
| 🐳 **Docker-оркестрация** | Готовый к деплою `docker-compose` с 5 независимыми сервисами (web, worker, beat, redis, postgres). |

---

## 🛠 Технологический стек

* **Backend & API:** FastAPI (полностью асинхронный) + Swagger UI (`/docs`)
* **Очереди & Фоновые задачи:** Celery + Redis (в качестве брокера сообщений и backend'а)
* **База данных:** PostgreSQL 15 + SQLAlchemy 2.0 (`asyncpg`)
* **Искусственный Интеллект:** OpenAI API (GPT-4)
* **Интеграции & Парсинг:** `feedparser` (для RSS) + `Telethon` (парсинг Telegram-каналов)
* **Публикация контента:** `aiogram` 3.x (Telegram Bot API)
* **Контейнеризация:** Docker + Docker Compose

---

## ⚙️ Быстрый старт (Развертывание)

### 1. Клонирование репозитория
```powershell
git clone https://github.com/Sergei1606/aibot.git
cd aibot
```

### 2. Настройка переменных окружения (`.env`)
Создайте файл `.env` в корневой директории проекта и заполните его по аналогии с `.env.example`:
```ini
TELEGRAM_BOT_TOKEN=123456:ABCdef...
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef
TELEGRAM_PHONE_NUMBER=+79161234567
DATABASE_URL=postgresql+asyncpg://aibot:aibot@db:5432/aibotdb
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=sk-proj-...
DEFAULT_TELEGRAM_CHANNEL=@your_channel_username
```

### 3. Запуск через Docker Compose
Запустит все необходимые базы данных, очереди и воркеры в изолированных контейнерах:
```bash
docker-compose up -d --build
```

### 4. Создание сессии Telethon (Авторизация для парсинга TG-каналов)
Чтобы парсить новости из Telegram, необходимо единоразово авторизоваться:
```powershell
python -c "
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv
import os
load_dotenv()

async def main():
    client = TelegramClient('data/session_tg', 
        int(os.getenv('TELEGRAM_API_ID')), 
        os.getenv('TELEGRAM_API_HASH'))
    await client.start(phone=os.getenv('TELEGRAM_PHONE_NUMBER'))
    print('✅ Сессия успешно создана')
    await client.disconnect()
asyncio.run(main())
"
```

### 5. Доступ к интерфейсам
- **Swagger API Документация:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Веб-интерфейс (Статистика):** [http://localhost:8000/](http://localhost:8000/)

---

## 📡 Основные API-эндпоинты

| Метод | URL | Описание |
|:---|:---|:---|
| **GET** | `/api/sources/` | Получить список источников новостей |
| **POST** | `/api/sources/` | Добавить новый источник (RSS или Telegram) |
| **GET** | `/api/keywords/` | Получить список ключевых слов для фильтрации |
| **POST** | `/api/keywords/` | Добавить ключевое слово |
| **GET** | `/api/news/` | Просмотр собранных новостей |
| **GET** | `/api/posts/` | Просмотр сгенерированных и опубликованных постов |
| **POST** | `/api/generate/` | Запустить ручную генерацию поста через AI |
| **POST** | `/api/tasks/parse` | Запустить задачу парсинга в Celery |
| **POST** | `/api/tasks/process-all` | Запуск полного цикла (парсинг → генерация → публикация) |
| **GET** | `/api/stats/` | Получить статистику бота |
| **GET** | `/health` | Health-check сервиса |

---

## ⏰ Расписание (Celery Beat)

- `full_news_cycle` — Запуск полного цикла: парсинг → генерация → публикация (Каждые **30 минут**)
- `publish_all_pending` — Отправка готовых, но еще не отправленных постов в Telegram (Каждые **5 минут**)

---

## 📁 Структура проекта

```text
aibot/
├── app/
│   ├── ai/              # Интеграция с OpenAI, генератор промптов
│   ├── api/             # FastAPI CRUD-эндпоинты и роутеры
│   ├── news_parser/     # Модули парсинга (RSS и Telethon для TG)
│   ├── telegram/        # Публикация через aiogram и клиент Telethon
│   ├── utils/           # Утилиты, фильтры, хелперы
│   ├── templates/       # HTML-шаблоны для веб-интерфейса
│   ├── main.py          # Точка входа FastAPI приложения
│   ├── tasks.py         # Определение фоновых задач Celery
│   ├── models.py        # SQLAlchemy ORM модели базы данных
│   ├── config.py        # Загрузка и валидация конфигурации (Pydantic)
│   └── database.py      # Настройка сессий подключения к PostgreSQL
├── data/                # Директория для хранения *.session файлов Telethon
├── tests/               # Pytest тесты
├── docker-compose.yml   # Docker манифест для всех сервисов
└── requirements.txt     # Python зависимости
```

---

## 📝 Чек-лист выполнения требований проекта (Project M4)

| № | Требование | Статус |
|:---:|:---|:---:|
| 1 | Сбор новостей (сайты / RSS) | ✅ |
| 2 | Сбор новостей (Telegram) | ✅ |
| 3 | Фильтрация по ключевым словам и антидубликат | ✅ |
| 4 | AI-генерация через OpenAI | ✅ |
| 5 | Публикация в Telegram через бота | ✅ |
| 6 | API-управление источниками и фильтрами (CRUD) | ✅ |
| 7 | Документация API (Swagger /docs/) | ✅ |
| 8 | Наличие Веб-интерфейса | ✅ |
| 9 | Оркестрация через Docker Compose | ✅ |
| 10 | Асинхронные задачи (Celery + Redis) | ✅ |

---
**Автор:** Sergei Pavljuk  
**Дата:** Май 2026
