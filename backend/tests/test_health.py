import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, settings
from app.main import app


def _configure_all(monkeypatch, tmp_path):
    """Point every dependency at a real, non-default value."""
    (tmp_path / "chroma.sqlite3").write_bytes(b"")
    monkeypatch.setattr(settings, "CHROMA_PERSIST_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_real_test_key")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://real-project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "real_anon_key")


async def _get_health() -> dict:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        return response.json()


@pytest.mark.asyncio
async def test_health_dependency_keys_unchanged():
    data = await _get_health()
    assert set(data["dependencies"]) == {"chromadb", "supabase", "groq"}


@pytest.mark.asyncio
async def test_health_default_settings_are_not_configured(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "CHROMA_PERSIST_DIR", str(tmp_path / "missing"))
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    for name in ("GROQ_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"):
        monkeypatch.setattr(settings, name, Settings.model_fields[name].default)

    data = await _get_health()
    assert data["dependencies"] == {
        "chromadb": "not_initialized",
        "supabase": "not_configured",
        "groq": "not_configured",
    }
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_empty_value_is_not_configured(monkeypatch, tmp_path):
    _configure_all(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    data = await _get_health()
    assert data["dependencies"]["groq"] == "not_configured"


@pytest.mark.asyncio
async def test_health_supabase_requires_url_and_key(monkeypatch, tmp_path):
    _configure_all(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "SUPABASE_KEY", Settings.model_fields["SUPABASE_KEY"].default)

    data = await _get_health()
    assert data["dependencies"]["supabase"] == "not_configured"


@pytest.mark.asyncio
async def test_health_missing_chroma_dir_is_not_created(monkeypatch, tmp_path):
    persist_dir = tmp_path / "chroma_db"
    monkeypatch.setattr(settings, "CHROMA_PERSIST_DIR", str(persist_dir))

    data = await _get_health()
    assert data["dependencies"]["chromadb"] == "not_initialized"
    assert not persist_dir.exists()


@pytest.mark.asyncio
async def test_health_empty_chroma_dir_is_not_initialized(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "CHROMA_PERSIST_DIR", str(tmp_path))

    data = await _get_health()
    assert data["dependencies"]["chromadb"] == "not_initialized"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("environment", ["development", "staging", "production"])
async def test_health_all_configured_is_healthy(monkeypatch, tmp_path, environment):
    _configure_all(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "ENVIRONMENT", environment)

    data = await _get_health()
    assert data["dependencies"] == {
        "chromadb": "initialized",
        "supabase": "configured",
        "groq": "configured",
    }
    assert data["status"] == "healthy"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "missing",
    [
        ("GROQ_API_KEY", ""),
        ("SUPABASE_URL", ""),
        ("CHROMA_PERSIST_DIR", "does-not-exist"),
    ],
)
async def test_health_development_stays_healthy_when_missing(monkeypatch, tmp_path, missing):
    _configure_all(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, missing[0], missing[1])

    data = await _get_health()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
@pytest.mark.parametrize("environment", ["staging", "production"])
@pytest.mark.parametrize(
    "missing",
    [
        ("GROQ_API_KEY", ""),
        ("SUPABASE_URL", ""),
        ("CHROMA_PERSIST_DIR", "does-not-exist"),
    ],
)
async def test_health_non_development_degraded_when_missing(monkeypatch, tmp_path, environment, missing):
    _configure_all(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "ENVIRONMENT", environment)
    monkeypatch.setattr(settings, missing[0], missing[1])

    data = await _get_health()
    assert data["status"] == "degraded"
