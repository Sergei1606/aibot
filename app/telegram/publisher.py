import requests
from app.config import config
from app.models import Post
from sqlalchemy.orm import Session
from datetime import datetime


class TelegramBotPublisher:
    """Публикация через Telegram Bot API"""

    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    def publish(self, channel: str, message: str) -> bool:
        """Отправляет сообщение в канал через бота"""
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": channel,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()

            if result.get("ok"):
                print(f"✅ Опубликовано в {channel}")
                return True
            else:
                print(f"❌ Ошибка API: {result.get('description')}")
                return False
        except Exception as e:
            print(f"❌ Ошибка публикации: {e}")
            return False


class PostPublisher:
    """Управление публикацией постов из БД"""

    def __init__(self, db: Session):
        self.db = db
        self.publisher = TelegramBotPublisher()

    def publish_post(self, post_id: str, channel: str = None) -> bool:
        """Публикует пост по ID в указанный канал"""
        # Сначала получаем объект поста
        post = self.db.query(Post).filter(Post.id == post_id).first()

        if not post:
            print(f"❌ Пост {post_id} не найден")
            return False

        # Теперь сравниваем атрибут объекта
        if post.status == "published":
            print(f"⚠️ Пост {post_id} уже опубликован")
            return False

        target_channel = channel or config.DEFAULT_TELEGRAM_CHANNEL

        success = self.publisher.publish(target_channel, post.generated_text)

        if success:
            post.status = "published"
            post.published_at = datetime.now()
            self.db.commit()
            print(f"✅ Пост {post_id} опубликован")
        else:
            post.status = "failed"
            self.db.commit()
            print(f"❌ Пост {post_id} не опубликован")

        return success

    def publish_pending_posts(self, channel: str = None) -> dict:
        """Публикует все посты со статусом 'generated'"""
        # Получаем список объектов постов
        pending = self.db.query(Post).filter(Post.status == "generated").all()

        published = 0
        failed = 0

        for post in pending:
            if self.publish_post(post.id, channel):
                published += 1
            else:
                failed += 1

        return {"published": published, "failed": failed, "total": len(pending)}