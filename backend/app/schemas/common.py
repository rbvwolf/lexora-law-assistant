from typing import Optional

from pydantic import BaseModel, Field

# Mandatory legal disclaimer per AGENTS.md Section 1, 5, and 6
LEGAL_DISCLAIMER: str = "Bu sistem bir AI asistanıdır; avukatlık hizmeti vermez."


class ErrorResponse(BaseModel):
    """Standardized error contract for all API responses."""

    error_code: str = Field(..., description="Unique error code identifier")
    message: str = Field(..., description="Human-readable explanation of the error")
    retry_after_seconds: Optional[int] = Field(
        default=None,
        description="Set on 503 LLM_RATE_LIMITED: seconds until a retry can succeed (also sent as Retry-After)",
    )


class HealthResponse(BaseModel):
    """Service health and dependency connectivity status."""

    status: str = Field(..., description="Overall service status (healthy / degraded)")
    environment: str = Field(..., description="Deployment environment")
    dependencies: dict[str, str] = Field(
        ...,
        description="Connectivity statuses of ChromaDB, Supabase, Groq",
    )
