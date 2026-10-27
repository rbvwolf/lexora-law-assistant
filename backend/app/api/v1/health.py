import os

from fastapi import APIRouter
from app.core.config import Settings, settings
from app.schemas.common import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])

CHROMA_DB_FILE = "chroma.sqlite3"


def _is_configured(*field_names: str) -> bool:
    """True if every field is non-empty and differs from its Settings default.

    Limit: this only tells whether a real value was supplied, not whether the
    key/URL is valid. No network call is made (protects Groq free-tier limits).
    """
    for name in field_names:
        value = getattr(settings, name)
        if not value or value == Settings.model_fields[name].default:
            return False
    return True


def _chromadb_status() -> str:
    """Check the persist dir on disk without opening a client.

    Opening chromadb.PersistentClient would create the directory and the
    SQLite file as a side effect; a real heartbeat will be added once
    rag_service owns a live client.
    """
    db_file = os.path.join(settings.CHROMA_PERSIST_DIR, CHROMA_DB_FILE)
    return "initialized" if os.path.isfile(db_file) else "not_initialized"


@router.get("", response_model=HealthResponse)
async def check_health() -> HealthResponse:
    """Return health status and dependency configuration state.

    In development, missing configuration keeps status "healthy" so local
    work without real keys is not reported as broken; in other environments
    any not_configured / not_initialized dependency makes it "degraded".
    """
    dependencies = {
        "chromadb": _chromadb_status(),
        "supabase": "configured" if _is_configured("SUPABASE_URL", "SUPABASE_KEY") else "not_configured",
        "groq": "configured" if _is_configured("GROQ_API_KEY") else "not_configured",
    }

    all_ready = all(value in ("configured", "initialized") for value in dependencies.values())
    is_development = settings.ENVIRONMENT == "development"

    return HealthResponse(
        status="healthy" if all_ready or is_development else "degraded",
        environment=settings.ENVIRONMENT,
        dependencies=dependencies,
    )
