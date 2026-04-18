from telethon import TelegramClient, errors
from app.config import config
from app.models import Post
from sqlalchemy.orm import Session
import asyncio


class TelegramPublisher:
    """Публикация постов в Telegram канал"""

    def __init__(self):
        self.client = None

    async def _get_client(self):
        """Создаёт клиент Telethon для публикации"""
        if self.client is None:
            self.client = TelegramClient(
                "session_publisher",
                config.TELEGRAM_API_ID,
                config.TELEGRAM_API_HASH
            )
            await self.client.start()
        return self.client

    async def publish_async(self, channel: str, message: str) -> bool:
        """
        Асинхронная публикация сообщения в канал
        Возвращает True при успехе, False при ошибке
        """
        try:
            client = await self._get_client()
            await client.send_message(channel, message)
            print(f"✅ Опубликовано в {channel}")
            return True
        except errors.FloodWaitError as e:
            print(f"⚠️ Flood wait: нужно подождать {e.seconds} секунд")
            return False
        except Exception as e:
            print(f"❌ Ошибка публикации: {e}")
            return False

    def publish(self, channel: str, message: str) -> bool:
        """Синхронная обёртка для публикации"""
        return asyncio.run(self.publish_async(channel, message))


class PostPublisher:
    """Управление публикацией постов из БД"""

    def __init__(self, db: Session):
        self.db = db
        self.publisher = TelegramPublisher()

    def publish_post(self, post_id: str, channel: str = None) -> bool:
        """
        Публикует пост по ID в указанный канал
        """
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            print(f"❌ Пост {post_id} не найден")
            return False

        if post.status == "published":
            print(f"⚠️ Пост {post_id} уже опубликован")
            return False

        target_channel = channel or config.DEFAULT_TELEGRAM_CHANNEL

        success = self.publisher.publish(target_channel, post.generated_text)

        if success:
            post.status = "published"
            post.published_at = __import__('datetime').datetime.now()
            self.db.commit()
            print(f"✅ Пост {post_id} опубликован")
        else:
            post.status = "failed"
            self.db.commit()
            print(f"❌ Пост {post_id} не опубликован")

        return success

    def publish_pending_posts(self, channel: str = None) -> dict:
        """
        Публикует все посты со статусом 'generated'
        Возвращает статистику
        """
        pending = self.db.query(Post).filter(Post.status == "generated").all()

        published = 0
        failed = 0

        for post in pending:
            if self.publish_post(post.id, channel):
                published += 1
            else:
                failed += 1

        return {"published": published, "failed": failed, "total": len(pending)}