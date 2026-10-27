from fastapi import APIRouter, HTTPException, status

from app.core.security import is_blank, mask_pii, sanitize_input
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["Chat"])


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
    intent, answer, extracted_params, missing_fields, suggested_template_id = (
        await llm_service.process_chat_message(masked_message, citations)
    )

    return ChatResponse(
        intent=intent,
        answer=answer,
        citations=citations if intent == "question_answering" else [],
        extracted_params=extracted_params,
        missing_fields=missing_fields,
        suggested_template_id=suggested_template_id,
    )
