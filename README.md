# 🤖 AI-генератор постов для Telegram

> **Автоматизированная система:** сбор новостей (RSS/Telegram) → AI-обработка (GPT) → Публикация в канал.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-5.3.4-37814A?logo=celery)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?logo=openai&logoColor=white)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---


## 🚀 Возможности

| Функция | Описание |
|:---|:---|
| 📰 **Парсинг** | Автосбор новостей из RSS (Habr, Postimees) и Telegram-каналов. |
| 🔍 **Фильтрация** | Умный фильтр по ключевым словам и проверка на дубликаты. |
| 🤖 **AI-генерация** | Переработка текста в увлекательные посты через OpenAI GPT. |
| 📤 **Публикация** | Мгновенная отправка готового контента в Telegram через Bot API. |
| ⏰ **Расписание** | Полностью автономная работа через Celery Beat. |
| 📡 **Control Panel** | Управление через Swagger UI (FastAPI). |

---

## 🛠 Технологии

- **Backend:** `FastAPI` (Асинхронность и скорость)
- **Очереди задач:** `Celery` + `Redis` (Брокер)
- **База данных:** `SQLite` (SQLAlchemy ORM)
- **AI Core:** `OpenAI API` (GPT-4/GPT-3.5)
- **Парсинг:** `feedparser` (RSS), `Telethon` (TG Scraping)
- **Логи:** `Loguru`

---

## 📁 Структура проекта

```text
aibot/
├── app/
│   ├── api/             # Маршруты FastAPI
│   ├── news_parser/     # Логика сбора данных (RSS, TG)
│   ├── telegram/        # Модули отправки сообщений
│   ├── utils/           # Фильтры и вспомогательные функции
│   ├── config.py        # Загрузка .env
│   ├── database.py      # Настройка SQLAlchemy
│   ├── models.py        # Схемы БД
│   ├── openai_client.py # Взаимодействие с ИИ
│   ├── tasks.py         # Фоновые задачи Celery
│   └── main.py          # Точка входа приложения
├── celery_worker.py     # Конфиг воркера
├── .env.example         # Шаблон настроек
└── requirements.txt     # Зависимости
```
---
## ⚙️ Установка и запуск

### 1. Подготовка окружения
#### Клонирование
- git clone [https://github.com/Sergei1606/aibot.git](https://github.com/Sergei1606/aibot.git)

- cd aibot

#### Виртуальное окружение
- python -m venv .venv
- source .venv/bin/activate  
- Для Windows: .venv\Scripts\activate

#### Зависимости
- pip install -r requirements.txt
---
### 2. Запуск инфраструктуры (Redis)
- docker run --name aibot-redis -p 6379:6379 -d redis
---
### 3. Запуск компонентов (в разных терминалах)
- API Сервер: uvicorn app.main:app --reload

- Worker: celery -A app.tasks worker --loglevel=info --pool=eventlet

- Scheduler: celery -A app.tasks beat --loglevel=info
---
## 🔧 Настройка окружения
- Создайте файл .env в корневой папке:
### База данных
- DATABASE_URL=sqlite:///./aibot.db

### API Ключи
- OPENAI_API_KEY=sk-your_key_here
- TELEGRAM_BOT_TOKEN=123456:ABC-DEF

### Настройки Telegram
- DEFAULT_TELEGRAM_CHANNEL=@your_channel_name
- REDIS_URL=redis://localhost:6379/0
---
## 📡 API Эндпоинты
После запуска документация доступна по адресу: http://localhost:8000/docs

- POST, /api/tasks/parse,    Принудительный запуск парсера
- POST, /api/tasks/process-all, Полный цикл: Парсинг → AI → Пост
- GET, /api/news/, Просмотр всех собранных новостей
- POST, /api/generate/, Ручная генерация поста из вашего текста
---
## ⏰ Автоматизация
В проекте настроены следующие интервалы:
- Каждые 30 минут: Сбор новостей и постановка в очередь на генерацию.

- Каждые 5 минут: Проверка и публикация готовых постов.
---
## 📝 Лицензия
- Распространяется под лицензией MIT. Подробности в файле LICENSE.
---