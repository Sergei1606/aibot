from openai import AsyncOpenAI
from app.config import config
from app.logger import logger
from app.ai.prompts import SYSTEM_PROMPT

class OpenAIClient:
    def __init__(self):
        self.api_key = config.OPENAI_API_KEY
        self.model = "gpt-3.5-turbo"
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OpenAI API key is missing. Posts won't be generated.")

    async def generate_post(self, text: str) -> str:
        if not self.client:
            return "Ошибка: не настроен ключ OpenAI."
            
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Ошибка генерации поста через OpenAI: {e}")
            return f"Краткое содержание (сгенерировано с ошибкой ИИ): {text[:200]}..."

openai_client = OpenAIClient()
