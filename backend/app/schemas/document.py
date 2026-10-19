from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.common import LEGAL_DISCLAIMER


class TemplateFieldSchema(BaseModel):
    """Schema descriptor for a field expected by a legal document template."""

    field_name: str = Field(..., description="Unique technical field key")
    label: str = Field(..., description="Human-readable label for UI form")
    field_type: str = Field(default="string", description="Type of field (string, number, date)")
    required: bool = Field(default=True, description="Whether field is strictly required")
    description: Optional[str] = Field(default=None, description="Guidance hint for user")


class TemplateSchema(BaseModel):
    """Active template metadata and its expected field schema."""

    template_id: str = Field(..., description="Unique template identifier (e.g. 'kira_ihtarname')")
    title: str = Field(..., description="Official title of the petition/notice template")
    domain: str = Field(..., description="Legal domain (e.g., 'Kira Hukuku', 'Tüketici Hukuku')")
    description: str = Field(..., description="Summary of legal purpose and usage")
    case_param_fields: List[TemplateFieldSchema] = Field(
        ...,
        description="Parameters extracted by LLM from the case facts",
    )
    pii_fields: List[TemplateFieldSchema] = Field(
        ...,
        description="Direct PII fields collected strictly via frontend mini-form",
    )


class TemplateListResponse(BaseModel):
    """List of available legal document templates."""

    templates: List[TemplateSchema] = Field(..., description="Active petition and notice templates")


class DocumentGenerateRequest(BaseModel):
    """Payload for generating .docx and .pdf legal documents."""

    template_id: str = Field(..., description="Target template identifier")
    case_params: Dict[str, Any] = Field(
        ...,
        description="Case parameters extracted from chat or confirmed by user",
    )
    pii: Dict[str, Any] = Field(
        ...,
        description="Direct PII (full name, TC ID, address, IBAN) from frontend mini-form",
    )


class DocumentGenerateResponse(BaseModel):
    """Dual export response with temporary download URLs."""

    file_id: str = Field(..., description="Unique identifier for generated document pair")
    docx_url: str = Field(..., description="Direct temporary download URL for .docx file")
    pdf_url: str = Field(..., description="Direct temporary download URL for .pdf file")
    expires_at: datetime = Field(..., description="Expiry timestamp after which files are auto-deleted")
    disclaimer: str = Field(default=LEGAL_DISCLAIMER, description="Mandatory legal disclaimer")
