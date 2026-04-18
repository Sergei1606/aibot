from openai import OpenAI
from app.config import config
from app.prompts import POST_GENERATION_PROMPT


class OpenAIClient:
    """Клиент для работы с OpenAI API"""

    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def generate_post(self, news_text: str, max_retries: int = 3) -> str:
        """
        Генерирует пост на основе новости
        Возвращает сгенерированный текст или сообщение об ошибке
        """
        if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "sk-ваш_ключ_здесь":
            # Если нет ключа, возвращаем заглушку
            return f"🔹 Тестовый режим (нет API ключа)\n\n{news_text[:300]}\n\n#новости #tech"

        prompt = POST_GENERATION_PROMPT.format(news_text=news_text[:1500])

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ты помощник для создания постов в Telegram."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content

            except Exception as e:
                print(f"Ошибка OpenAI (попытка {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    # Последняя попытка — возвращаем упрощённую версию новости
                    return f"🔹 {news_text[:400]}\n\n#новости #tech"

        # Страховочный return (на случай, если цикл по каким-то причинам не вернул значение)
        return news_text[:400]


# Создаём глобальный экземпляр (ВНЕ класса, на уровне модуля)
openai_client = OpenAIClient()