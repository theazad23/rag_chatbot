import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client() -> AsyncClient:
    """Create a test client using the recommended ASGI transport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="session")
def event_loop_policy():
    """Default event loop policy for Linux/Unix systems."""
    return asyncio.DefaultEventLoopPolicy()