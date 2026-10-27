from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.common import LEGAL_DISCLAIMER

FieldType = Literal["string", "number", "date", "tc_id", "iban"]


class TemplateFieldSchema(BaseModel):
    """Schema descriptor for a field expected by a legal document template."""

    field_name: str = Field(..., description="Unique technical field key")
    label: str = Field(..., description="Human-readable label for UI form")
    field_type: FieldType = Field(
        default="string",
        description="Type of field (string, number, date, tc_id, iban)",
    )
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
    pii: Dict[str, Annotated[str, Field(max_length=500)]] = Field(
        ...,
        description="Direct PII from frontend mini-form; keys defined by the template's pii_fields",
    )


class TemplateFieldErrors(BaseModel):
    """Template field validation result. Holds field NAMES only, never values (KVKK)."""

    missing: List[str] = Field(default_factory=list, description="Required fields not provided")
    unknown: List[str] = Field(default_factory=list, description="PII keys not defined by the template")
    invalid: List[str] = Field(default_factory=list, description="Fields failing type/format checks")

    @property
    def has_errors(self) -> bool:
        return bool(self.missing or self.unknown or self.invalid)

    def to_message(self) -> str:
        parts = []
        if self.missing:
            parts.append(f"Eksik: {', '.join(self.missing)}")
        if self.unknown:
            parts.append(f"Tanımsız: {', '.join(self.unknown)}")
        if self.invalid:
            parts.append(f"Geçersiz: {', '.join(self.invalid)}")
        return "; ".join(parts)


class DocumentGenerateResponse(BaseModel):
    """Dual export response with temporary download URLs."""

    file_id: str = Field(..., description="Unique identifier for generated document pair")
    docx_url: str = Field(..., description="Direct temporary download URL for .docx file")
    pdf_url: str = Field(..., description="Direct temporary download URL for .pdf file")
    expires_at: datetime = Field(..., description="Expiry timestamp after which files are auto-deleted")
    disclaimer: str = Field(default=LEGAL_DISCLAIMER, description="Mandatory legal disclaimer")
