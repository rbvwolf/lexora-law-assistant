"""Build the .docx document templates in settings.TEMPLATES_DIR with python-docx.

Why generate instead of editing in Word: docxtpl only replaces a {{ tag }} that sits inside a
single run, and Word splits runs on spell-check / revision marks. Here every tag is written by
one add_run() call, so it stays intact. tests/test_doc_service.py fails if a tag is ever split.

Usage (from backend/):
    python -m tools.build_doc_templates
"""

import argparse
from pathlib import Path
from typing import List, Tuple

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from app.core.config import settings
from app.schemas.common import LEGAL_DISCLAIMER

FONT_NAME = "Times New Roman"

# A paragraph is a list of (text, bold) segments; each segment becomes exactly one run.
Segment = Tuple[str, bool]


def _setup_document() -> Document:
    doc = Document()
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    for side in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(section, side, Cm(2.5))

    normal = doc.styles["Normal"]
    normal.font.name = FONT_NAME
    normal.font.size = Pt(12)
    # East Asian slot too, so Word never falls back to another font for any glyph
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT_NAME)
    normal.paragraph_format.space_after = Pt(6)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run(f"Taslak belge. {LEGAL_DISCLAIMER}")
    run.font.size = Pt(8)
    run.italic = True
    return doc


def _add_paragraph(
    doc: Document,
    segments: List[Segment],
    align: WD_ALIGN_PARAGRAPH = WD_ALIGN_PARAGRAPH.JUSTIFY,
    first_line_indent: bool = False,
) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = align
    if first_line_indent:
        paragraph.paragraph_format.first_line_indent = Cm(1.25)
    for text, bold in segments:
        paragraph.add_run(text).bold = bold


def build_kira_artis_itiraz_ihtarname(out_dir: Path) -> Path:
    doc = _setup_document()
    center = WD_ALIGN_PARAGRAPH.CENTER
    left = WD_ALIGN_PARAGRAPH.LEFT

    _add_paragraph(doc, [("{{ noter_ili }}", True), (" Nöbetçi Noterliğine", True)], align=center)
    _add_paragraph(doc, [("İHTARNAME", True)], align=center)

    _add_paragraph(doc, [("KEŞİDECİ (Kiracı): ", True), ("{{ kiraci_ad_soyad }}", False), ("{{ kiraci_tc_ibare }}", False)], align=left)
    _add_paragraph(doc, [("Adres: ", True), ("{{ kiraci_adres }}", False)], align=left)
    _add_paragraph(doc, [("MUHATAP (Kiraya Veren): ", True), ("{{ kiraya_veren_ad_soyad }}", False), ("{{ kiraya_veren_tc_ibare }}", False)], align=left)
    _add_paragraph(doc, [("Adres: ", True), ("{{ kiraya_veren_adres }}", False)], align=left)
    _add_paragraph(doc, [("KİRALANAN: ", True), ("{{ tasinmaz_adresi }}", False)], align=left)
    _add_paragraph(
        doc,
        [
            ("KONU: ", True),
            ("{{ kira_baslangic_tarihi }}", False),
            (
                " başlangıç tarihli kira sözleşmesine ilişkin olarak talep edilen kira artışının, "
                "6098 sayılı Türk Borçlar Kanunu m. 344 uyarınca yasal sınırı aştığının ve bu sınırı "
                "aşan kısmın kabul edilmediğinin bildirilmesidir.",
                False,
            ),
        ],
    )

    _add_paragraph(doc, [("AÇIKLAMALAR:", True)], align=left)
    _add_paragraph(
        doc,
        [
            ("1. Yukarıda adresi belirtilen taşınmazı, ", False),
            ("{{ kira_baslangic_tarihi }}", False),
            (" başlangıç tarihli kira sözleşmesi uyarınca kiracı sıfatıyla kullanmaktayım. Mevcut aylık kira bedeli ", False),
            ("{{ mevcut_kira_tutari }}", True),
            (" TL'dir.", True),
        ],
        first_line_indent=True,
    )
    _add_paragraph(
        doc,
        [
            ("2. Tarafınızca yeni kira dönemi için aylık ", False),
            ("{{ talep_edilen_kira_tutari }}", True),
            (" TL", True),
            (" kira bedeli talep edilmiştir. Bu talep, mevcut kira bedeline göre %", False),
            ("{{ talep_artis_orani }}", False),
            (" oranında bir artışa karşılık gelmektedir.", False),
        ],
        first_line_indent=True,
    )
    _add_paragraph(
        doc,
        [
            (
                "3. 6098 sayılı Türk Borçlar Kanunu'nun 344. maddesinin birinci fıkrası uyarınca, tarafların "
                "yenilenen kira dönemlerinde uygulanacak kira bedeline ilişkin anlaşmaları, bir önceki kira "
                "yılında tüketici fiyat endeksindeki on iki aylık ortalamalara göre değişim oranını geçmemek "
                "koşuluyla geçerlidir. Bu oran %",
                False,
            ),
            ("{{ tufe_oran }}", False),
            (" olup, buna göre yeni kira döneminde uygulanabilecek azami aylık kira bedeli ", False),
            ("{{ yasal_azami_kira }}", True),
            (" TL", True),
            ("'dir.", False),
        ],
        first_line_indent=True,
    )
    _add_paragraph(
        doc,
        [
            (
                "4. Açıklanan nedenlerle, yasal sınırı aşan kira artışı talebinizi kabul etmediğimi; yeni kira "
                "döneminde aylık kira bedelini yasal sınır olan ",
                False,
            ),
            ("{{ yasal_azami_kira }}", True),
            (" TL", True),
            (" üzerinden ödeyeceğimi bildiririm.", False),
        ],
        first_line_indent=True,
    )

    _add_paragraph(doc, [("SONUÇ:", True)], align=left)
    _add_paragraph(
        doc,
        [
            (
                "İşbu ihtarnamenin bir suretinin muhataba tebliğini, bir suretinin dairenizde saklanmasını ve "
                "tebliğ şerhini havi bir suretinin tarafıma verilmesini saygılarımla talep ederim.",
                False,
            )
        ],
        first_line_indent=True,
    )

    right = WD_ALIGN_PARAGRAPH.RIGHT
    _add_paragraph(doc, [("{{ belge_tarihi }}", False)], align=right)
    _add_paragraph(doc, [("Keşideci", True)], align=right)
    _add_paragraph(doc, [("{{ kiraci_ad_soyad }}", False)], align=right)
    _add_paragraph(doc, [("İmza", False)], align=right)

    out_path = out_dir / "kira_artis_itiraz_ihtarname.docx"
    doc.save(str(out_path))
    return out_path


BUILDERS = [build_kira_artis_itiraz_ihtarname]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", default=settings.TEMPLATES_DIR, help="Output directory (default: TEMPLATES_DIR)")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for build in BUILDERS:
        print(f"Wrote {build(out_dir)}")


if __name__ == "__main__":
    main()
