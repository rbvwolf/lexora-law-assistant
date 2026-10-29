import asyncio
import logging
import math
import os
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from docxtpl import DocxTemplate
from fpdf import FPDF

from app.core.config import settings
from app.schemas.document import FieldType, TemplateFieldErrors, TemplateFieldSchema, TemplateSchema
from app.services.doc_layouts import (
    FIRST_LINE_INDENT_CM,
    FONT_SIZE_PT,
    FOOTER_FONT_SIZE_PT,
    PAGE_MARGIN_CM,
    SPACE_AFTER_PT,
    DocumentLayout,
    fill_tags,
    get_layout,
)

logger = logging.getLogger(__name__)

# Temporary directory for generated documents (auto-deleted after expiration)
STORAGE_TEMP_DIR = Path("storage/temp")
STORAGE_TEMP_DIR.mkdir(parents=True, exist_ok=True)

TC_ID_RE = re.compile(r"^\d{11}$")
IBAN_TR_RE = re.compile(r"^TR\d{24}$")

KIRA_ARTIS_TEMPLATE_ID = "kira_artis_itiraz_ihtarname"
TUFE_ORAN_MAX = Decimal("200")

# How often the background task deletes expired files (see app.main lifespan)
DOCUMENT_SWEEP_INTERVAL = timedelta(minutes=10)
DOWNLOADABLE_SUFFIXES = (".docx", ".pdf")

PDF_FONT_FAMILY = "LiberationSerif"
PDF_FONT_FILES = {
    "": "LiberationSerif-Regular.ttf",
    "B": "LiberationSerif-Bold.ttf",
    "I": "LiberationSerif-Italic.ttf",
}
_PDF_ALIGN = {"left": "L", "center": "C", "right": "R", "justify": "J"}
_PT_TO_MM = 25.4 / 72


class DocumentAssetMissingError(RuntimeError):
    """A real template's .docx or PDF font is missing outside development. Message holds no paths."""


def _now() -> datetime:
    """Single clock for expiry; tests replace it instead of waiting."""
    return datetime.now(timezone.utc)


def _is_expired(path: Path, now_ts: float) -> bool:
    """Expiry rule: file mtime (set to the generation time) + DOCUMENT_TTL_MINUTES."""
    return path.stat().st_mtime + settings.DOCUMENT_TTL_MINUTES * 60 <= now_ts


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _to_decimal(value: Any) -> Decimal:
    """Convert a value that already passed the "number" check to Decimal without float noise."""
    return Decimal(str(value).strip())


def _format_tr_number(value: Decimal) -> str:
    """Format as Turkish money/percent notation: 19501.2 -> '19.501,20'."""
    return f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _format_tr_date(value: str) -> str:
    """ISO date -> 'GG.AA.YYYY'."""
    return date.fromisoformat(value).strftime("%d.%m.%Y")


def _yasal_azami_kira(mevcut: Decimal, tufe_oran: Decimal) -> Decimal:
    """TBK m. 344/1 ceiling from the user-supplied CPI rate, rounded to kuruş."""
    return (mevcut * (1 + tufe_oran / 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _check_kira_artis(case_params: Dict[str, Any]) -> List[str]:
    """Cross-field rules for the rent-increase objection. Returns invalid field NAMES only."""
    mevcut = _to_decimal(case_params["mevcut_kira_tutari"])
    talep = _to_decimal(case_params["talep_edilen_kira_tutari"])
    tufe_oran = _to_decimal(case_params["tufe_oran"])

    invalid = []
    if mevcut <= 0:
        invalid.append("mevcut_kira_tutari")
    if not Decimal("0") <= tufe_oran <= TUFE_ORAN_MAX:
        invalid.append("tufe_oran")
    if invalid:
        return invalid
    # A request within the legal ceiling is lawful; the notice would wrongly call it excessive.
    if talep <= _yasal_azami_kira(mevcut, tufe_oran):
        invalid.append("talep_edilen_kira_tutari")
    return invalid


def _tc_ibare(value: Optional[str]) -> str:
    return f" (T.C. Kimlik No: {value})" if value else ""


def _kira_artis_context(case_params: Dict[str, Any], pii: Dict[str, str]) -> Dict[str, str]:
    """Render context for the rent-increase objection. Keys must match the .docx tags exactly."""
    mevcut = _to_decimal(case_params["mevcut_kira_tutari"])
    talep = _to_decimal(case_params["talep_edilen_kira_tutari"])
    tufe_oran = _to_decimal(case_params["tufe_oran"])
    talep_artis_orani = ((talep - mevcut) / mevcut * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "noter_ili": str(case_params["noter_ili"]).strip(),
        "kira_baslangic_tarihi": _format_tr_date(case_params["kira_baslangic_tarihi"]),
        "mevcut_kira_tutari": _format_tr_number(mevcut),
        "talep_edilen_kira_tutari": _format_tr_number(talep),
        "talep_artis_orani": _format_tr_number(talep_artis_orani),
        "tufe_oran": _format_tr_number(tufe_oran),
        "yasal_azami_kira": _format_tr_number(_yasal_azami_kira(mevcut, tufe_oran)),
        "belge_tarihi": date.today().strftime("%d.%m.%Y"),
        "kiraci_ad_soyad": pii["kiraci_ad_soyad"],
        "kiraci_tc_ibare": _tc_ibare(pii.get("kiraci_tc")),
        "kiraci_adres": pii["kiraci_adres"],
        "kiraya_veren_ad_soyad": pii["kiraya_veren_ad_soyad"],
        "kiraya_veren_tc_ibare": _tc_ibare(pii.get("kiraya_veren_tc")),
        "kiraya_veren_adres": pii["kiraya_veren_adres"],
        "tasinmaz_adresi": pii["tasinmaz_adresi"],
    }


# Per-template cross-field rules (run only when the involved fields passed the basic checks)
_CROSS_FIELD_RULES: Dict[str, Tuple[Tuple[str, ...], Callable[[Dict[str, Any]], List[str]]]] = {
    KIRA_ARTIS_TEMPLATE_ID: (("mevcut_kira_tutari", "talep_edilen_kira_tutari", "tufe_oran"), _check_kira_artis),
}

# Templates rendered from data/templates/<template_id>.docx; others still produce mock files
_RENDER_CONTEXT_BUILDERS: Dict[str, Callable[[Dict[str, Any], Dict[str, str]], Dict[str, str]]] = {
    KIRA_ARTIS_TEMPLATE_ID: _kira_artis_context,
}


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
            return math.isfinite(value)
        if isinstance(value, str):
            try:
                return math.isfinite(float(value))
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
    """Service handling dual direct export (.docx via docxtpl, .pdf via fpdf2) and expiry."""

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
            KIRA_ARTIS_TEMPLATE_ID: TemplateSchema(
                template_id=KIRA_ARTIS_TEMPLATE_ID,
                title="Fahiş Kira Artışına İtiraz İhtarnamesi",
                domain="Kira Hukuku",
                description=(
                    "Kiraya verenin yenilenen kira döneminde TBK m. 344 uyarınca TÜFE on iki aylık ortalamalarına "
                    "göre değişim oranını aşan artış talebine kiracının itirazı. Geçici dönemsel sınırlamalar ve "
                    "5 yılı aşan sözleşmeler için uygun değildir, hukukçu doğrulaması gerekir."
                ),
                case_param_fields=[
                    TemplateFieldSchema(field_name="kira_baslangic_tarihi", label="Kira Sözleşmesi Başlangıç Tarihi", field_type="date", required=True),
                    TemplateFieldSchema(field_name="mevcut_kira_tutari", label="Mevcut Aylık Kira Bedeli (TL)", field_type="number", required=True),
                    TemplateFieldSchema(field_name="talep_edilen_kira_tutari", label="Talep Edilen Aylık Kira Bedeli (TL)", field_type="number", required=True),
                    TemplateFieldSchema(
                        field_name="tufe_oran",
                        label="TÜFE 12 Aylık Ortalama Değişim Oranı (%)",
                        field_type="number",
                        required=True,
                        description=(
                            "TÜİK tarafından ilan edilen, bir önceki kira yılına ait TÜFE on iki aylık ortalamalara "
                            "göre değişim oranı. Kullanıcı girer; sistem bu oranı tahmin etmez."
                        ),
                    ),
                    TemplateFieldSchema(field_name="noter_ili", label="İhtarnamenin Gönderileceği Noterlik (İl)", field_type="string", required=True),
                ],
                pii_fields=[
                    TemplateFieldSchema(field_name="kiraci_ad_soyad", label="Kiracı Adı Soyadı", field_type="string", required=True),
                    TemplateFieldSchema(field_name="kiraci_tc", label="Kiracı TC Kimlik No", field_type="tc_id", required=False),
                    TemplateFieldSchema(field_name="kiraci_adres", label="Kiracı Tebligat Adresi", field_type="string", required=True),
                    TemplateFieldSchema(field_name="kiraya_veren_ad_soyad", label="Kiraya Veren Adı Soyadı / Unvanı", field_type="string", required=True),
                    TemplateFieldSchema(field_name="kiraya_veren_tc", label="Kiraya Veren TC Kimlik No", field_type="tc_id", required=False),
                    TemplateFieldSchema(field_name="kiraya_veren_adres", label="Kiraya Veren Tebligat Adresi", field_type="string", required=True),
                    TemplateFieldSchema(field_name="tasinmaz_adresi", label="Kiralanan Taşınmaz Adresi", field_type="string", required=True),
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

        rule = _CROSS_FIELD_RULES.get(template.template_id)
        if rule:
            involved, check = rule
            already_failed = set(errors.missing) | set(errors.invalid)
            if not already_failed.intersection(involved):
                errors.invalid.extend(check(case_params))
        return errors

    def template_path(self, template_id: str) -> Path:
        """Location of a template's .docx file under settings.TEMPLATES_DIR."""
        return Path(settings.TEMPLATES_DIR) / f"{template_id}.docx"

    def build_render_context(
        self, template_id: str, case_params: Dict[str, Any], pii: Dict[str, str]
    ) -> Optional[Dict[str, str]]:
        """Formatted context for a real .docx template, or None if the template is still mocked."""
        builder = _RENDER_CONTEXT_BUILDERS.get(template_id)
        return builder(case_params, pii) if builder else None

    @staticmethod
    def _render_docx(template_path: Path, context: Dict[str, str], out_path: Path) -> None:
        """Render via docxtpl to a temp name, then rename so a half-written file is never served."""
        tmp_path = out_path.with_name(out_path.name + ".tmp")
        doc = DocxTemplate(str(template_path))
        # autoescape keeps values like "Yılmaz & Oğulları" from corrupting the XML
        doc.render(context, autoescape=True)
        doc.save(str(tmp_path))
        os.replace(tmp_path, out_path)

    def font_paths(self) -> Dict[str, Path]:
        """PDF font files under settings.FONTS_DIR, keyed by fpdf2 style."""
        return {style: Path(settings.FONTS_DIR) / name for style, name in PDF_FONT_FILES.items()}

    def _fonts_available(self) -> bool:
        return all(p.is_file() for p in self.font_paths().values())

    def _render_pdf(self, layout: DocumentLayout, context: Dict[str, str], out_path: Path) -> None:
        """Render the shared layout with fpdf2 (same context as the .docx, no second calculation)."""
        footer_text = layout.footer

        class _LayoutPDF(FPDF):
            def footer(self) -> None:
                self.set_y(-15)
                self.set_font(PDF_FONT_FAMILY, "I", FOOTER_FONT_SIZE_PT)
                self.cell(0, 10, footer_text, align="C")

        margin_mm = PAGE_MARGIN_CM * 10
        pdf = _LayoutPDF(format="A4", unit="mm")
        pdf.set_margins(margin_mm, margin_mm, margin_mm)
        pdf.set_auto_page_break(True, margin=margin_mm)
        for style, path in self.font_paths().items():
            pdf.add_font(PDF_FONT_FAMILY, style, str(path))
        # Metadata: template title only, never PII
        pdf.set_title(layout.pdf_title)
        pdf.set_author("lexora")
        pdf.set_creator("lexora")
        pdf.add_page()
        pdf.set_font(PDF_FONT_FAMILY, "", FONT_SIZE_PT)

        # Segments are written one by one (no markdown), so "**" in user input stays literal text
        with pdf.text_columns() as columns:
            for spec in layout.paragraphs:
                with columns.paragraph(
                    text_align=_PDF_ALIGN[spec.align],
                    bottom_margin=SPACE_AFTER_PT * _PT_TO_MM,
                    first_line_indent=FIRST_LINE_INDENT_CM * 10 if spec.first_line_indent else 0,
                ) as paragraph:
                    for text, bold in spec.segments:
                        pdf.set_font(PDF_FONT_FAMILY, "B" if bold else "", FONT_SIZE_PT)
                        paragraph.write(fill_tags(text, context))

        tmp_path = out_path.with_name(out_path.name + ".tmp")
        pdf.output(str(tmp_path))
        os.replace(tmp_path, out_path)

    @staticmethod
    def _write_mock(path: Path, kind: str, template_id: str) -> None:
        # Mock placeholders carry the template id only, never case data or PII
        prefix = "%PDF-1.4 " if kind == "PDF" else ""
        path.write_text(f"{prefix}Mock {kind} Document for template {template_id}", encoding="utf-8")

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
        generated_at = _now()
        expires_at = generated_at + timedelta(minutes=settings.DOCUMENT_TTL_MINUTES)

        # File names carry only the random file_id, never PII
        docx_filename = f"{file_id}.docx"
        pdf_filename = f"{file_id}.pdf"

        docx_path = STORAGE_TEMP_DIR / docx_filename
        pdf_path = STORAGE_TEMP_DIR / pdf_filename

        context = self.build_render_context(template_id, case_params, pii)
        layout = get_layout(template_id) if context is not None else None
        template_path = self.template_path(template_id)
        render_docx = context is not None and template_path.is_file()
        render_pdf = layout is not None and self._fonts_available()

        if context is not None and not (render_docx and render_pdf):
            missing = [name for name, ok in (("docx_template", render_docx), ("pdf_fonts", render_pdf)) if not ok]
            if settings.ENVIRONMENT != "development":
                raise DocumentAssetMissingError(f"Missing document assets for {template_id}: {missing}")
            logger.warning("Missing document assets for %s: %s; writing mock files (development only)", template_id, missing)

        docx_job = (
            (self._render_docx, template_path, context, docx_path)
            if render_docx
            else (self._write_mock, docx_path, "DOCX", template_id)
        )
        pdf_job = (
            (self._render_pdf, layout, context, pdf_path)
            if render_pdf
            else (self._write_mock, pdf_path, "PDF", template_id)
        )
        # Both renderers are synchronous; run them in parallel off the event loop
        results = await asyncio.gather(
            asyncio.to_thread(*docx_job), asyncio.to_thread(*pdf_job), return_exceptions=True
        )
        failures = [r for r in results if isinstance(r, BaseException)]
        if failures:
            # Never leave half a pair (or a .tmp) behind
            for path in (docx_path, pdf_path):
                for candidate in (path, path.with_name(path.name + ".tmp")):
                    candidate.unlink(missing_ok=True)
            raise failures[0]

        # mtime = generation time, so expiry is exactly expires_at (survives restarts)
        ts = generated_at.timestamp()
        for path in (docx_path, pdf_path):
            os.utime(path, (ts, ts))

        docx_url = f"/api/v1/documents/download/{docx_filename}"
        pdf_url = f"/api/v1/documents/download/{pdf_filename}"

        return file_id, docx_url, pdf_url, expires_at

    def resolve_download_path(self, file_id: str) -> Optional[Path]:
        """Resolve a downloadable file, preventing directory traversal.

        Only .docx/.pdf are served (never .tmp). An expired file is deleted on the spot,
        so it is never served even if the sweeper has not run yet.
        """
        safe_name = os.path.basename(file_id)
        if not safe_name.endswith(DOWNLOADABLE_SUFFIXES):
            return None
        candidate = STORAGE_TEMP_DIR / safe_name
        try:
            if not candidate.is_file():
                return None
            if _is_expired(candidate, _now().timestamp()):
                candidate.unlink(missing_ok=True)
                return None
        except FileNotFoundError:
            return None
        return candidate

    def sweep_expired(self) -> int:
        """Delete every expired regular file in STORAGE_TEMP_DIR (incl. stale .tmp). Returns count.

        Uses mtime, so files left over from before a restart are handled too. If
        DOCUMENT_TTL_MINUTES changes between restarts, the new TTL applies to old files.
        """
        now_ts = _now().timestamp()
        try:
            entries = list(STORAGE_TEMP_DIR.iterdir())
        except FileNotFoundError:
            return 0
        removed = 0
        for path in entries:
            try:
                if path.is_file() and _is_expired(path, now_ts):
                    path.unlink()
                    removed += 1
            except FileNotFoundError:
                continue  # another worker or a download got there first
            except OSError as exc:
                logger.warning("Could not delete an expired document file: %s", type(exc).__name__)
        if removed:
            logger.info("Deleted %d expired document file(s)", removed)
        return removed

    async def sweep_expired_async(self) -> int:
        return await asyncio.to_thread(self.sweep_expired)

    async def run_sweeper(self) -> None:
        """Sweep immediately (startup), then every DOCUMENT_SWEEP_INTERVAL until cancelled."""
        while True:
            try:
                await self.sweep_expired_async()
            except Exception as exc:  # keep the loop alive; the next round retries
                logger.warning("Expired document sweep failed: %s", type(exc).__name__)
            await asyncio.sleep(DOCUMENT_SWEEP_INTERVAL.total_seconds())


# Singleton instance
doc_service = DocService()
