"""Groq 429 / outage handling: bounded retries in llm_service and 503 answers from /chat/message.

No network: the Groq client and sleeps are replaced.
"""

from unittest.mock import AsyncMock, MagicMock

import groq
import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app
from app.services import llm_service as llm_module
from app.services.llm_service import (
    LLMRateLimitedError,
    LLMUnavailableError,
    _create_with_retries,
    _retry_after_seconds,
)

_REQUEST = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")


def _rate_limit(headers=None):
    response = httpx.Response(429, headers=headers or {}, request=_REQUEST)
    return groq.RateLimitError("Rate limit reached", response=response, body=None)


def _server_error():
    return groq.InternalServerError("over capacity", response=httpx.Response(503, request=_REQUEST), body=None)


def _client(*outcomes):
    """A Groq client whose create() raises/returns the given outcomes in order."""
    client = MagicMock()
    client.chat.completions.create = AsyncMock(side_effect=list(outcomes))
    return client


@pytest.fixture
def waits(monkeypatch):
    recorded = []

    async def fake_sleep(seconds):
        recorded.append(seconds)

    monkeypatch.setattr(llm_module, "_sleep", fake_sleep)
    monkeypatch.setattr(settings, "GROQ_RATE_LIMIT_MAX_WAIT_SECONDS", 4.0)
    monkeypatch.setattr(settings, "GROQ_RATE_LIMIT_MAX_RETRIES", 2)
    return recorded


# ---------------------------------------------------------------------------
# Retry-After parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "headers, expected",
    [
        ({"retry-after": "24"}, 24.0),
        ({"retry-after": "1.5"}, 1.5),
        ({"retry-after-ms": "2500", "retry-after": "3"}, 2.5),
        ({"retry-after": "Wed, 21 Oct 2026 07:28:00 GMT"}, None),
        ({}, None),
    ],
)
def test_retry_after_seconds(headers, expected):
    assert _retry_after_seconds(_rate_limit(headers)) == expected


# ---------------------------------------------------------------------------
# _create_with_retries
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_short_retry_after_is_waited_then_succeeds(waits):
    client = _client(_rate_limit({"retry-after": "1.5"}), "completion")
    assert await _create_with_retries(client, {}) == "completion"
    assert waits == [1.5]


@pytest.mark.asyncio
async def test_long_retry_after_fails_fast_without_waiting(waits):
    client = _client(_rate_limit({"retry-after": "24"}))
    with pytest.raises(LLMRateLimitedError) as exc_info:
        await _create_with_retries(client, {})
    assert exc_info.value.retry_after_seconds == 24.0
    assert waits == []
    assert client.chat.completions.create.await_count == 1


@pytest.mark.asyncio
async def test_wait_budget_is_total_not_per_retry(waits):
    # 3 s then another 3 s would exceed the 4 s budget: stop after the first wait
    client = _client(_rate_limit({"retry-after": "3"}), _rate_limit({"retry-after": "3"}), "never")
    with pytest.raises(LLMRateLimitedError):
        await _create_with_retries(client, {})
    assert waits == [3.0]


@pytest.mark.asyncio
async def test_retry_count_is_bounded(waits):
    client = _client(*[_rate_limit({"retry-after": "0.1"})] * 5)
    with pytest.raises(LLMRateLimitedError):
        await _create_with_retries(client, {})
    assert len(waits) == 2
    assert client.chat.completions.create.await_count == 3


@pytest.mark.asyncio
async def test_missing_retry_after_uses_one_second(waits):
    client = _client(_rate_limit(), "completion")
    assert await _create_with_retries(client, {}) == "completion"
    assert waits == [1.0]


@pytest.mark.asyncio
async def test_timeout_is_not_retried(waits):
    client = _client(groq.APITimeoutError(request=_REQUEST), "never")
    with pytest.raises(LLMUnavailableError):
        await _create_with_retries(client, {})
    assert client.chat.completions.create.await_count == 1


@pytest.mark.asyncio
async def test_transient_server_error_is_retried(waits):
    client = _client(_server_error(), groq.APIConnectionError(request=_REQUEST), "completion")
    assert await _create_with_retries(client, {}) == "completion"
    assert len(waits) == 2


@pytest.mark.asyncio
async def test_persistent_server_error_becomes_unavailable(waits):
    client = _client(*[_server_error()] * 5)
    with pytest.raises(LLMUnavailableError):
        await _create_with_retries(client, {})
    assert client.chat.completions.create.await_count == 3


def test_sdk_retries_are_disabled(monkeypatch):
    monkeypatch.setattr(llm_module, "_groq_client", None)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test_key_not_real")
    client = llm_module._get_groq_client()
    try:
        assert client.max_retries == 0
        assert client.timeout == settings.GROQ_TIMEOUT_SECONDS
    finally:
        monkeypatch.setattr(llm_module, "_groq_client", None)


# ---------------------------------------------------------------------------
# /api/v1/chat/message
# ---------------------------------------------------------------------------


async def _post_chat(monkeypatch, error):
    monkeypatch.setattr(llm_module.llm_service, "process_chat_message", AsyncMock(side_effect=error))
    from app.api.v1 import chat as chat_module

    monkeypatch.setattr(chat_module.rag_service, "retrieve_citations", AsyncMock(return_value=[]))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.post("/api/v1/chat/message", json={"session_id": "s", "message": "Kira artışı ne kadar olabilir?"})


@pytest.mark.asyncio
async def test_chat_rate_limited_returns_503_with_retry_after(monkeypatch):
    response = await _post_chat(monkeypatch, LLMRateLimitedError(23.2))
    assert response.status_code == 503
    assert response.headers["retry-after"] == "24"
    body = response.json()
    assert body["error_code"] == "LLM_RATE_LIMITED"
    assert body["retry_after_seconds"] == 24
    assert "24 saniye" in body["message"]


@pytest.mark.asyncio
async def test_chat_rate_limited_without_retry_after_uses_default(monkeypatch):
    response = await _post_chat(monkeypatch, LLMRateLimitedError(None))
    assert response.status_code == 503
    assert response.json()["retry_after_seconds"] == 20


@pytest.mark.asyncio
async def test_chat_daily_limit_wait_is_passed_on_in_minutes(monkeypatch):
    # Groq's tokens-per-day limit: "Please try again in 17m13.776s"
    response = await _post_chat(monkeypatch, LLMRateLimitedError(1033.776))
    body = response.json()
    assert body["retry_after_seconds"] == 1034
    assert response.headers["retry-after"] == "1034"
    assert "18 dakika" in body["message"]
    assert "limiti doldu" in body["message"]


@pytest.mark.asyncio
async def test_chat_rate_limited_retry_after_is_capped_at_one_day(monkeypatch):
    response = await _post_chat(monkeypatch, LLMRateLimitedError(10 * 24 * 3600))
    assert response.json()["retry_after_seconds"] == 24 * 3600


@pytest.mark.asyncio
async def test_chat_llm_unavailable_returns_503(monkeypatch):
    response = await _post_chat(monkeypatch, LLMUnavailableError())
    assert response.status_code == 503
    body = response.json()
    assert body["error_code"] == "LLM_UNAVAILABLE"
    assert "Traceback" not in response.text
