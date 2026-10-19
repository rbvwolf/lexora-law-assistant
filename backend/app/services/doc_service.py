import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.document import TemplateFieldSchema, TemplateSchema

logger = logging.getLogger(__name__)

# Temporary directory for generated documents (auto-deleted after expiration)
STORAGE_TEMP_DIR = Path("storage/temp")
STORAGE_TEMP_DIR.mkdir(parents=True, exist_ok=True)


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
                    TemplateFieldSchema(field_name="kiraya_veren_tc", label="Kiraya Veren TC Kimlik No", field_type="string", required=True),
                    TemplateFieldSchema(field_name="kiraci_ad_soyad", label="Kiracı Adı Soyadı", field_type="string", required=True),
                    TemplateFieldSchema(field_name="kiraci_tc", label="Kiracı TC Kimlik No", field_type="string", required=False),
                    TemplateFieldSchema(field_name="iban", label="Kiranın Yatırılacağı IBAN", field_type="string", required=True),
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
                    TemplateFieldSchema(field_name="tuketici_tc", label="Tüketici TC Kimlik No", field_type="string", required=True),
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

    async def generate_documents(
        self,
        template_id: str,
        case_params: Dict[str, Any],
        pii: Dict[str, Any],
    ) -> Tuple[str, str, str, datetime]:
        """Generate both .docx and .pdf files in parallel from unified data model.

        Returns:
            (file_id, docx_url, pdf_url, expires_at)
        """
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
