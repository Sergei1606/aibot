🐳 Docker команды
# Запуск всех сервисов
docker-compose up -d

# Запуск с пересборкой образов
docker-compose up -d --build

# Остановка всех сервисов
docker-compose down

# Остановка с удалением volumes (очистка БД)
docker-compose down -v

# Просмотр статуса контейнеров
docker-compose logs -f


# Просмотр логов всех сервисов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f beat

# Перезапуск конкретного сервиса
docker-compose restart worker

# Выполнение команды в контейнере
docker-compose exec web bash
docker-compose exec worker python -c "print('test')"

# Очистка неиспользуемых контейнеров и образов
docker system prune -a

🔧 Telegram сессии
# Создание новой сессии
python -c "
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv
import os
load_dotenv()

async def main():
    client = TelegramClient('data/session_name',
        int(os.getenv('TELEGRAM_API_ID')),
        os.getenv('TELEGRAM_API_HASH'))
    await client.start()
    print('✅ Сессия создана')
    await client.disconnect()
asyncio.run(main())
"

# Проверка существующей сессии
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
    await client.start()
    me = await client.get_me()
    print(f'Авторизован как: {me.first_name}')
    await client.disconnect()
asyncio.run(main())
"

# Показать все диалоги (чаты/каналы)
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
    await client.start()
    async for dialog in client.iter_dialogs():
        print(f'{dialog.name}: {dialog.entity.id}')
    await client.disconnect()
asyncio.run(main())
"

📦 Python и зависимости
# Активация виртуального окружения
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Установка зависимостей
pip install -r requirements.txt

# Обновление зависимостей
pip install --upgrade -r requirements.txt

# Сохранение текущих зависимостей
pip freeze > requirements.txt

# Установка конкретного пакета
pip install telethon celery redis fastapi uvicorn

# Запуск тестов
python -m pytest tests/


🚀 Запуск приложения
# Локальный запуск (без Docker)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Или через Python
python -m app.main

# Запуск Celery worker (локально)
celery -A app.utils.tasks worker --loglevel=info

# Запуск Celery beat (планировщик)
celery -A app.utils.tasks beat --loglevel=info

# Запуск Redis (локально)
redis-server

# Запуск всего через docker-compose
docker-compose up -d



🗄️ База данных
bash
# Подключение к PostgreSQL в контейнере
docker-compose exec db psql -U postgres -d aibot

# Основные SQL команды внутри psql
\l  # список БД
\dt # список таблиц
\d table_name # структура таблицы
\q  # выход

# Резервное копирование БД
docker-compose exec db pg_dump -U postgres aibot > backup.sql

# Восстановление БД
docker-compose exec -T db psql -U postgres aibot < backup.sql

# Очистка таблиц (осторожно!)
docker-compose exec db psql -U postgres -d aibot -c "TRUNCATE TABLE tasks;"


📝 Работа с логами
bash
# Просмотр файлов логов
ls logs/

# Очистка логов
rm -rf logs/*.log

# Мониторинг лога в реальном времени (Linux/Mac)
tail -f logs/app.log

# Поиск ошибок в логах
grep -r "ERROR" logs/
🧪 Тестирование
bash
# Тест Celery
python test_celery.py

# Тест Redis
python test_redis.py

# Тест подключения к Telegram
python -c "
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv
import os
load_dotenv()

async def test():
    client = TelegramClient('data/session_tg',
        int(os.getenv('TELEGRAM_API_ID')),
        os.getenv('TELEGRAM_API_HASH'))
    await client.start()
    print('✅ Telegram работает')
    await client.disconnect()
asyncio.run(test())
"
🔄 Git команды
bash
# Статус изменений
git status

# Добавить все изменения
git add .

# Создать коммит
git commit -m "Описание изменений"

# Отправить на удалённый репозиторий
git push origin main

# Получить последние изменения
git pull origin main

# Просмотр истории коммитов
git log --oneline --graph --all


🛠️ Утилиты
bash
# Очистка кэша Python
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Просмотр занятого места
du -sh *

# Проверка переменных окружения
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(dict(os.environ))" | grep TELEGRAM

# Перезапуск всех сервисов (после изменений)
docker-compose down && docker-compose up -d --build

# Проверка доступности Redis
docker-compose exec redis redis-cli ping

# Вход в контейнер Redis
docker-compose exec redis redis-cli

# Вход в контейнер PostgreSQL
docker-compose exec db bash
⚡ Быстрые команды для разработки
bash
# Полный рестарт проекта
docker-compose down && docker-compose up -d --build && docker-compose logs -f

# Проверка всех сервисов
docker-compose ps && echo "---" && docker-compose logs --tail=20

# Очистка и пересборка
docker system prune -f && docker-compose up -d --build

# Запуск только необходимых сервисов
docker-compose up -d redis db
docker-compose up -d web worker beat

💡 Полезные алиасы для PowerShell (.bashrc/.zshrc)
bash
# Добавьте в ~/.bashrc или ~/.zshrc (Linux/Mac)
alias dc='docker-compose'
alias dcu='docker-compose up -d'
alias dcd='docker-compose down'
alias dcl='docker-compose logs -f'
alias dce='docker-compose exec'
alias dps='docker-compose ps'

# Для Windows PowerShell (в profile.ps1)
function dcu { docker-compose up -d }
function dcd { docker-compose down }
function dcl { docker-compose logs -f }