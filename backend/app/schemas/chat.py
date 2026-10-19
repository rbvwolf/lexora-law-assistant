from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.common import LEGAL_DISCLAIMER


class Citation(BaseModel):
    """Statutory citation reference retrieved from legal corpora."""

    article_id: str = Field(..., description="Unique article identifier (e.g., 'TBK-M344')")
    law_name: str = Field(..., description="Full statutory law name")
    text_snippet: str = Field(..., description="Extracted relevant text excerpt")


class ChatRequest(BaseModel):
    """User incoming chat message payload."""

    session_id: str = Field(..., description="Unique conversational session identifier")
    message: str = Field(..., min_length=1, description="User's query or case description")


class ChatResponse(BaseModel):
    """Standardized response contract for /api/v1/chat/message."""

    intent: Literal["question_answering", "document_generation", "out_of_scope"] = Field(
        ...,
        description="Classified user intention",
    )
    answer: str = Field(
        ...,
        description="Legal explanation with citations (if Q&A) or guidance response",
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="List of statutory references supporting the answer",
    )
    extracted_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured case parameters extracted from user message",
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Required fields the agent still needs to solicit from user",
    )
    suggested_template_id: Optional[str] = Field(
        default=None,
        description="Suggested document template id when intent is document_generation",
    )
    disclaimer: str = Field(
        default=LEGAL_DISCLAIMER,
        description="Mandatory legal disclaimer",
    )
