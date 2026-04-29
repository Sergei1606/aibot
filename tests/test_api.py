import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Проверка health check эндпоинта"""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_get_stats_empty(client: AsyncClient):
    """Проверка получения статистики"""
    response = await client.get("/api/stats/")
    assert response.status_code == 200
    data = response.json()
    # Проверяем, что есть нужные поля
    assert "posts_today" in data or "total_news" in data or "queued_posts" in data

@pytest.mark.asyncio
async def test_ui_renders(client: AsyncClient):
    """Проверка загрузки веб-интерфейса"""
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]