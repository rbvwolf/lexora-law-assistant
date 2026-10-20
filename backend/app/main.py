import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import chat, documents, health
from app.core.config import settings
from app.schemas.common import ErrorResponse

# Configure root logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("lexora")

# FastAPI App Instance
app = FastAPI(
    title="lexora: AI Powered Law Assistant API",
    description="Backend REST API for Turkish statutory RAG, intent classification, and dynamic legal document generation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware for Next.js frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler for structured HTTPException
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Return standard JSON error format per AGENTS.md Section 6."""
    if isinstance(exc.detail, dict) and "error_code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": "HTTP_ERROR", "message": str(exc.detail)},
    )


# Global Exception Handler for Pydantic Request Validation Errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return standard JSON error format for validation errors per AGENTS.md Section 6."""
    error_messages = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        error_messages.append(f"{loc}: {err.get('msg', 'Geçersiz alan')}")

    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "; ".join(error_messages),
        },
    )


# Global Unhandled Exception Handler
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all unhandled error handler protecting internal stack traces."""
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Beklenmeyen bir sunucu hatası meydana geldi. Lütfen tekrar deneyiniz.",
        },
    )


# Mount API v1 Routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "project": "lexora: AI Powered Law Assistant",
        "api_v1_docs": "/docs",
        "health": "/api/v1/health",
    }
