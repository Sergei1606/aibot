import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_get_stats_empty(client: AsyncClient):
    # Учитываем, что префикс роутера отсутствует в main.py, но сам роутер импортирован без префикса
    # В main.py: app.include_router(endpoints.router)
    # В endpoints.py: @router.get("/stats/")
    response = await client.get("/stats/")
    assert response.status_code == 200
    data = response.json()
    assert data["total_news"] == 0
    assert data["published_today"] == 0
    assert data["pending_posts"] == 0

@pytest.mark.asyncio
async def test_ui_renders(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert "AI News Bot Dashboard" in response.text
