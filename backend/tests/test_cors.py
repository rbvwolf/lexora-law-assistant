"""CORS tests: Vite dev origins allowed, others refused, no credentials, safe origin parsing."""

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app

ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
DISALLOWED_ORIGIN = "http://evil.example"


def _preflight_headers(origin: str) -> dict:
    # What a browser sends before fetch(..., {method: "POST", headers: {"Content-Type": "application/json"}})
    return {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }


@pytest.mark.parametrize("origin", ALLOWED_ORIGINS)
@pytest.mark.asyncio
async def test_preflight_allowed_origin(origin):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options("/api/v1/chat/message", headers=_preflight_headers(origin))
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
        assert "POST" in response.headers["access-control-allow-methods"]
        assert "content-type" in response.headers["access-control-allow-headers"].lower()
        assert "access-control-allow-credentials" not in response.headers


@pytest.mark.asyncio
async def test_preflight_disallowed_origin():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.options("/api/v1/chat/message", headers=_preflight_headers(DISALLOWED_ORIGIN))
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers
        assert "access-control-allow-credentials" not in response.headers


@pytest.mark.asyncio
async def test_simple_request_allowed_origin_gets_header():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert "access-control-allow-credentials" not in response.headers


@pytest.mark.asyncio
async def test_simple_request_disallowed_origin_gets_no_header():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health", headers={"Origin": DISALLOWED_ORIGIN})
        # The server still answers; the browser blocks the page from reading it
        assert response.status_code == 200
        assert "access-control-allow-origin" not in response.headers


def test_default_origins_cover_vite_and_legacy_port():
    default = Settings.model_fields["CORS_ORIGINS"].default
    assert default == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_origins_from_env_json(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://lexora.vercel.app"]')
    assert Settings().CORS_ORIGINS == ["https://lexora.vercel.app"]


def test_trailing_slash_is_stripped(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://lexora.vercel.app/", " http://localhost:5173 "]')
    assert Settings().CORS_ORIGINS == ["https://lexora.vercel.app", "http://localhost:5173"]


@pytest.mark.parametrize("value", ['["*"]', '["https://lexora.vercel.app", "*"]', '["*/"]'])
def test_wildcard_origin_rejected(monkeypatch, value):
    monkeypatch.setenv("CORS_ORIGINS", value)
    with pytest.raises(ValidationError):
        Settings()
