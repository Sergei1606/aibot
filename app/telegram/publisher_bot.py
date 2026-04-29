from telethon import TelegramClient
from app.config import config
from app.models import Post
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.logger import logger


class TelegramBotPublisher:
    """Публикация через Telethon (Bot)"""

    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.api_id = config.TELEGRAM_API_ID
        self.api_hash = config.TELEGRAM_API_HASH
        self.client = None

    async def _get_client(self):
        if self.client is None:
            self.client = TelegramClient("session_publisher", self.api_id, self.api_hash)
            await self.client.start(bot_token=self.bot_token)
        return self.client

    async def publish(self, channel: str, message: str) -> bool:
        """Отправляет сообщение в канал через Telethon"""
        try:
            client = await self._get_client()
            await client.send_message(channel, message, parse_mode="html")
            logger.info(f"✅ Опубликовано в {channel}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка публикации: {e}")
            return False


class PostPublisher:
    """Управление публикацией постов из БД"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.publisher = TelegramBotPublisher()

    async def publish_post(self, post_id: str, channel: str = None) -> bool:
        """Публикует пост по ID в указанный канал"""
        result = await self.db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()

        if not post:
            logger.error(f"❌ Пост {post_id} не найден")
            return False

        if post.status == "published":
            logger.info(f"⚠️ Пост {post_id} уже опубликован")
            return False

        target_channel = channel or config.DEFAULT_TELEGRAM_CHANNEL

        success = await self.publisher.publish(target_channel, post.generated_text)

        if success:
            post.status = "published"
            post.published_at = datetime.now()
            await self.db.commit()
            logger.info(f"✅ Пост {post_id} опубликован")
        else:
            post.status = "failed"
            await self.db.commit()
            logger.error(f"❌ Пост {post_id} не опубликован")

        return success

    async def publish_pending_posts(self, channel: str = None) -> dict:
        """Публикует все посты со статусом 'generated'"""
        result = await self.db.execute(select(Post).where(Post.status == "generated"))
        pending = result.scalars().all()

        published = 0
        failed = 0

        for post in pending:
            if await self.publish_post(post.id, channel):
                published += 1
            else:
                failed += 1

        return {"published": published, "failed": failed, "total": len(pending)}