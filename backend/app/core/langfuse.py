import logging
from typing import Any, Callable, Dict, Optional
from functools import wraps

from app.core.config import settings
from app.core.security import mask_pii

logger = logging.getLogger(__name__)

# Global Langfuse client reference
_langfuse_client: Optional[Any] = None


def get_langfuse_client() -> Optional[Any]:
    """Initialize and return Langfuse client if configured; else return None (graceful no-op)."""
    global _langfuse_client
    if _langfuse_client is not None:
        return _langfuse_client

    if not settings.LANGFUSE_SECRET_KEY:
        logger.info("Langfuse secret key not configured; observability will run in no-op mode.")
        return None

    try:
        from langfuse import Langfuse  # type: ignore

        _langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        logger.info("Langfuse client initialized successfully.")
        return _langfuse_client
    except Exception as e:
        logger.warning(f"Failed to initialize Langfuse client ({e}); falling back to no-op mode.")
        return None


def trace_llm_call(name: str):
    """Decorator to log LLM calls to Langfuse with strict PII masking applied."""

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            client = get_langfuse_client()
            if not client:
                return await func(*args, **kwargs)

            # Mask arguments before logging
            masked_kwargs: Dict[str, Any] = {}
            for k, v in kwargs.items():
                if isinstance(v, str):
                    masked_kwargs[k] = mask_pii(v)
                else:
                    masked_kwargs[k] = v

            trace = client.trace(name=name, metadata={"environment": settings.ENVIRONMENT})
            try:
                result = await func(*args, **kwargs)
                trace.update(output="[Execution Success]")
                return result
            except Exception as exc:
                trace.update(output=f"[Execution Error]: {str(exc)}")
                raise exc

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            client = get_langfuse_client()
            if not client:
                return func(*args, **kwargs)

            trace = client.trace(name=name, metadata={"environment": settings.ENVIRONMENT})
            try:
                result = func(*args, **kwargs)
                trace.update(output="[Execution Success]")
                return result
            except Exception as exc:
                trace.update(output=f"[Execution Error]: {str(exc)}")
                raise exc

        # Return appropriate wrapper based on coroutine check
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
