import math
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.core.security import is_blank, mask_pii, sanitize_input
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMRateLimitedError, LLMUnavailableError, llm_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["Chat"])

# Retry-After sent to the client when Groq gave none, and the range it is kept in. Groq's daily
# token limit (TPD) answers with waits of many minutes, so the real value is passed on, not capped low.
DEFAULT_RETRY_AFTER_SECONDS = 20
MAX_RETRY_AFTER_SECONDS = 24 * 60 * 60


def _client_retry_after(seconds: Optional[float]) -> int:
    """Whole seconds (1..86400) the client should wait; Groq's value rounded up, or a default."""
    if seconds is None:
        return DEFAULT_RETRY_AFTER_SECONDS
    return min(MAX_RETRY_AFTER_SECONDS, max(1, math.ceil(seconds)))


def _rate_limited_message(retry_after: int) -> str:
    """Short waits (per-minute limit) in seconds; long ones (daily limit) in minutes."""
    if retry_after < 120:
        return f"Şu anda çok yoğunuz. Lütfen yaklaşık {retry_after} saniye sonra tekrar deneyin."
    minutes = math.ceil(retry_after / 60)
    return (
        "Yapay zekâ servisinin kullanım limiti doldu. "
        f"Lütfen yaklaşık {minutes} dakika sonra tekrar deneyin."
    )


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest) -> ChatResponse:
    """Chat message pipeline:

    1. Sanitize user input (detect prompt injections)
    2. Mask accidental PII in free text before calling LLM
    3. Retrieve legal citations via article-based RAG
    4. Process intent classification and parameter extraction via LLM
    """
    # Step 1: Reject whitespace/invisible-only messages, then injection check
    if is_blank(request.message):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "EMPTY_MESSAGE", "message": "Mesaj boş olamaz."},
        )

    is_safe, sanitized_or_refusal = sanitize_input(request.message)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "PROMPT_INJECTION_DETECTED", "message": sanitized_or_refusal},
        )

    # Step 2: Mask accidental PII before LLM sees the text
    masked_message = mask_pii(sanitized_or_refusal)

    # Step 3: Retrieve relevant law article citations
    citations = await rag_service.retrieve_citations(masked_message, top_k=5)

    # Step 4: LLM intent classification and parameter extraction
    try:
        intent, answer, extracted_params, missing_fields, suggested_template_id = (
            await llm_service.process_chat_message(masked_message, citations)
        )
    except LLMRateLimitedError as exc:
        retry_after = _client_retry_after(exc.retry_after_seconds)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "LLM_RATE_LIMITED",
                "message": _rate_limited_message(retry_after),
                "retry_after_seconds": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        ) from exc
    except LLMUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "LLM_UNAVAILABLE",
                "message": "Yapay zekâ servisine şu anda ulaşılamıyor. Lütfen biraz sonra tekrar deneyin.",
            },
        ) from exc

    return ChatResponse(
        intent=intent,
        answer=answer,
        citations=citations if intent == "question_answering" else [],
        extracted_params=extracted_params,
        missing_fields=missing_fields,
        suggested_template_id=suggested_template_id,
    )
