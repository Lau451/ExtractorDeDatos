import pytest
from httpx import ASGITransport, AsyncClient

from src.core.job_store import job_store
from src.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def clear_job_store():
    """Reset job store between tests to ensure test isolation."""
    yield
    async with job_store._lock:
        job_store._store.clear()
