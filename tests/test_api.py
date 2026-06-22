"""
Integration tests for FastAPI endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app


@pytest.fixture
def transport():
    """Create ASGI transport for testing."""
    return ASGITransport(app=app)


@pytest.fixture
async def client(transport):
    """Create async HTTP client for testing."""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """Tests for GET /health."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        """Health check should return 200."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_response_format(self, client):
        """Health check should return expected fields."""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
        assert "timestamp" in data


class TestHistoryEndpoint:
    """Tests for GET /history."""

    @pytest.mark.asyncio
    async def test_history_returns_200(self, client):
        """History should return 200 (even if empty)."""
        response = await client.get("/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestReportEndpoint:
    """Tests for GET /report/{id}."""

    @pytest.mark.asyncio
    async def test_nonexistent_report_returns_404(self, client):
        """Should return 404 for nonexistent sessions."""
        response = await client.get("/report/nonexistent-session-id")
        assert response.status_code == 404


class TestResearchEndpoint:
    """Tests for POST /research."""

    @pytest.mark.asyncio
    async def test_empty_query_rejected(self, client):
        """Should reject empty or too-short queries."""
        response = await client.post("/research", json={"query": "ab"})
        assert response.status_code == 422  # Validation error
