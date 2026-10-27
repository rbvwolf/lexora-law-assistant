import logging
import os
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.document import FieldType, TemplateFieldErrors, TemplateFieldSchema, TemplateSchema

logger = logging.getLogger(__name__)

# Temporary directory for generated documents (auto-deleted after expiration)
STORAGE_TEMP_DIR = Path("storage/temp")
STORAGE_TEMP_DIR.mkdir(parents=True, exist_ok=True)

TC_ID_RE = re.compile(r"^\d{11}$")
IBAN_TR_RE = re.compile(r"^TR\d{24}$")


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _matches_type(value: Any, field_type: FieldType) -> bool:
    """Format check per field type (no TC checksum by design)."""
    if field_type == "tc_id":
        return isinstance(value, str) and bool(TC_ID_RE.match(value))
    if field_type == "iban":
        return isinstance(value, str) and bool(IBAN_TR_RE.match(re.sub(r"\s+", "", value)))
    if field_type == "number":
        if isinstance(value, bool):
            return False
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value)
                return True
            except ValueError:
                return False
        return False
    if field_type == "date":
        if not isinstance(value, str):
            return False
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False
    return True


class DocService:
    """Service handling dual direct export (.docx via docxtpl, .pdf via WeasyPrint/fpdf2)."""

    def __init__(self):
        self.templates: Dict[str, TemplateSchema] = {
            "kira_ihtarname_temerrut": TemplateSchema(
                template_id="kira_ihtarname_temerrut",
                title="Kira Bedelinin Ödenmemesi Nedeniyle Temerrüt İhtarnamesi",
                domain="Kira Hukuku",
                description="Kiracının vadesi gelen kira bedellerini ödememesi halinde TBK m. 315 uyarınca 30 günlük ödeme süresi tanınması ve tahliye ihtarı.",
                case_param_fields=[
                    TemplateFieldSchema(field_name="kira_tutari", label="Aylık Kira Bedeli (TL)", field_type="number", required=True),
                    TemplateFieldSchema(field_name="gecikilen_aylar", label="Ödenmeyen Aylar", field_type="string", required=True),
                    TemplateFieldSchema(field_name="odeme_suresi_gun", label="Ödeme İçin Verilen Süre (Gün)", field_type="number", required=True),
                    TemplateFieldSchema(field_name="tasinmaz_adresi", label="Kiralanan Taşınmaz Adresi", field_type="string", required=True),
                ],
                pii_fields=[
                    TemplateFieldSchema(field_name="kiraya_veren_ad_soyad", label="Kiraya Veren Adı Soyadı", field_type="string", required=True),
                    TemplateFieldSchema(field_name="kiraya_veren_tc", label="Kiraya Veren TC Kimlik No", field_type="tc_id", required=True),
                    TemplateFieldSchema(field_name="kiraci_ad_soyad", label="Kiracı Adı Soyadı", field_type="string", required=True),
                    TemplateFieldSchema(field_name="kiraci_tc", label="Kiracı TC Kimlik No", field_type="tc_id", required=False),
                    TemplateFieldSchema(field_name="iban", label="Kiranın Yatırılacağı IBAN", field_type="iban", required=True),
                ],
            ),
            "tuketici_ayipli_mal_ihtarname": TemplateSchema(
                template_id="tuketici_ayipli_mal_ihtarname",
                title="Ayıplı Mal Nedeniyle Bedel İadesi / Değişim Talebi",
                domain="Tüketici Hukuku",
                description="Satın alınan maldaki ayıbın satıcıya bildirimi ve TKHK m. 11 uyarınca bedel iadesi veya değişim talebi.",
                case_param_fields=[
                    TemplateFieldSchema(field_name="urun_adi", label="Satın Alınan Ürün", field_type="string", required=True),
                    TemplateFieldSchema(field_name="fatura_tarihi", label="Fatura/Teslim Tarihi", field_type="date", required=True),
                    TemplateFieldSchema(field_name="ayipli_durum_ozeti", label="Mevcut Arıza / Ayıp Özeti", field_type="string", required=True),
                    TemplateFieldSchema(field_name="secimlik_hak", label="Talep Edilen Hak (Bedel İadesi / Değişim)", field_type="string", required=True),
                ],
                pii_fields=[
                    TemplateFieldSchema(field_name="tuketici_ad_soyad", label="Tüketici Adı Soyadı", field_type="string", required=True),
                    TemplateFieldSchema(field_name="tuketici_tc", label="Tüketici TC Kimlik No", field_type="tc_id", required=True),
                    TemplateFieldSchema(field_name="satici_unvan", label="Satıcı Firma / Şirket Unvanı", field_type="string", required=True),
                ],
            ),
        }

    def list_templates(self) -> List[TemplateSchema]:
        """Return active templates."""
        return list(self.templates.values())

    def get_template(self, template_id: str) -> Optional[TemplateSchema]:
        """Fetch template schema by ID."""
        return self.templates.get(template_id)

    def validate_fields(
        self,
        template: TemplateSchema,
        case_params: Dict[str, Any],
        pii: Dict[str, str],
    ) -> TemplateFieldErrors:
        """Validate payload against the template's field definitions.

        Unknown PII keys are rejected; unknown case_params keys are not (they come
        from LLM output and are filtered out in generate_documents instead).
        Result carries field names only, never values.
        """
        errors = TemplateFieldErrors()
        pii_names = {f.field_name for f in template.pii_fields}
        errors.unknown = sorted(k for k in pii if k not in pii_names)

        for fields, payload in ((template.case_param_fields, case_params), (template.pii_fields, pii)):
            for field in fields:
                value = payload.get(field.field_name)
                if _is_blank(value):
                    if field.required:
                        errors.missing.append(field.field_name)
                    continue
                if not _matches_type(value, field.field_type):
                    errors.invalid.append(field.field_name)
        return errors

    def filter_case_params(self, template: TemplateSchema, case_params: Dict[str, Any]) -> Dict[str, Any]:
        """Drop case_params keys not defined by the template, logging dropped key names only."""
        allowed = {f.field_name for f in template.case_param_fields}
        dropped = sorted(k for k in case_params if k not in allowed)
        if dropped:
            logger.info("Dropped undefined case_params keys for %s: %s", template.template_id, dropped)
        return {k: v for k, v in case_params.items() if k in allowed}

    async def generate_documents(
        self,
        template_id: str,
        case_params: Dict[str, Any],
        pii: Dict[str, str],
    ) -> Tuple[str, str, str, datetime]:
        """Generate both .docx and .pdf files in parallel from unified data model.

        Returns:
            (file_id, docx_url, pdf_url, expires_at)
        """
        template = self.get_template(template_id)
        if template:
            case_params = self.filter_case_params(template, case_params)

        file_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(hours=2)

        # Merge parameters into single unified rendering context
        unified_context = {**case_params, **pii, "file_id": file_id}

        # Create mock file assets in temporary directory for immediate testing
        docx_filename = f"{file_id}.docx"
        pdf_filename = f"{file_id}.pdf"

        docx_path = STORAGE_TEMP_DIR / docx_filename
        pdf_path = STORAGE_TEMP_DIR / pdf_filename

        # Write initial placeholder bytes so download endpoints work immediately
        docx_path.write_text(f"Mock DOCX Document for template {template_id}\nContext: {unified_context}", encoding="utf-8")
        pdf_path.write_text(f"%PDF-1.4 Mock PDF Document for template {template_id}\nContext: {unified_context}", encoding="utf-8")

        docx_url = f"/api/v1/documents/download/{docx_filename}"
        pdf_url = f"/api/v1/documents/download/{pdf_filename}"

        return file_id, docx_url, pdf_url, expires_at

    def resolve_download_path(self, file_id: str) -> Optional[Path]:
        """Resolve and validate filepath for download, preventing directory traversal."""
        safe_name = os.path.basename(file_id)
        candidate = STORAGE_TEMP_DIR / safe_name
        if candidate.exists() and candidate.is_file():
            return candidate
        return None


# Singleton instance
doc_service = DocService()
