from fastapi import APIRouter
from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def check_health() -> HealthResponse:
    """Return health status and dependency connectivity verification."""
    # Check dependencies (mock checks for starter skeleton)
    dependencies = {
        "chromadb": "connected" if settings.CHROMA_PERSIST_DIR else "unconfigured",
        "supabase": "connected" if settings.SUPABASE_URL else "unconfigured",
        "groq": "connected" if settings.GROQ_API_KEY else "unconfigured",
    }

    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        dependencies=dependencies,
    )
