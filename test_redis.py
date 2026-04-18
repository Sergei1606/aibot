import redis
import os
from dotenv import load_dotenv

load_dotenv()

try:
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    r.set("test_key", "Hello Redis!")
    value = r.get("test_key")
    print(f"✅ Redis работает! Получено значение: {value.decode('utf-8')}")
except Exception as e:
    print(f"❌ Ошибка: {e}")