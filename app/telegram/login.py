import asyncio
import os
from telethon import TelegramClient
from app.config import config

async def main():
    print("=== Авторизация Telethon для Docker ===")
    print("Этот скрипт создаст файлы сессий в папке data/, которые потом будут использоваться в Docker.")
    
    os.makedirs("data", exist_ok=True)
    
    # Авторизация для парсера (если нужен)
    # sources = ["Tech Morning", "Rus Delfie"]
    # Для каждого источника можно создать свою сессию, но обычно нужна одна для парсера
    
    # Авторизация для бота (публикация)
    print("\n[1/2] Настройка сессии для публикации (publisher)...")
    publisher_client = TelegramClient("data/session_publisher", config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH)
    
    # Для бота (если используется BOT_TOKEN)
    if config.TELEGRAM_BOT_TOKEN:
        print("Подключение через токен бота...")
        await publisher_client.start(bot_token=config.TELEGRAM_BOT_TOKEN)
        print("✅ Бот успешно авторизован!")
    else:
        print("Бот-токен не найден, пропускаем...")
        
    await publisher_client.disconnect()
    
    print("\n[2/2] Настройка сессии для парсинга (пользовательский аккаунт)...")
    # Создадим одну общую сессию для парсера (или для каждого канала)
    # В tg_parser.py сейчас f"data/session_{self.source_name}"
    # Для упрощения можно попросить пользователя войти для каждого источника,
    # но логичнее использовать одну сессию пользователя для всех чтений.
    # Давайте сделаем для Tech Morning
    parser_client = TelegramClient("data/session_Tech Morning", config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH)
    
    print("Для парсинга нужен номер телефона. Введите его (в международном формате, например +79991234567):")
    await parser_client.start()
    print("✅ Аккаунт для парсинга успешно авторизован!")
    
    await parser_client.disconnect()
    
    print("\n🎉 Готово! Файлы .session сохранены в папке data/. Теперь вы можете запускать docker-compose up -d")

if __name__ == "__main__":
    asyncio.run(main())
