"""Single source of truth for document text and layout.

Both outputs are built from these definitions:
    - .docx: tools/build_doc_templates.py writes data/templates/<template_id>.docx, which
      docxtpl then fills ({{ tag }} segments stay inside one run).
    - .pdf: doc_service renders the same paragraphs with fpdf2, substituting the tags from
      the same render context.

Changing the text here requires re-running the template builder; tests compare the
committed .docx against these definitions.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple

from app.schemas.common import LEGAL_DISCLAIMER

Align = Literal["left", "center", "right", "justify"]

TAG_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")

FONT_SIZE_PT = 12
FOOTER_FONT_SIZE_PT = 8
PAGE_MARGIN_CM = 2.5
SPACE_AFTER_PT = 6
FIRST_LINE_INDENT_CM = 1.25


@dataclass(frozen=True)
class Paragraph:
    # Each (text, bold) segment becomes exactly one run in the .docx
    segments: List[Tuple[str, bool]]
    align: Align = "justify"
    first_line_indent: bool = False


@dataclass(frozen=True)
class DocumentLayout:
    paragraphs: List[Paragraph]
    footer: str
    pdf_title: str


def fill_tags(text: str, context: Dict[str, str]) -> str:
    """Replace {{ tag }} with its context value (PDF path; docxtpl handles the .docx)."""
    return TAG_RE.sub(lambda m: context[m.group(1)], text)


FOOTER_TEXT = f"Taslak belge. {LEGAL_DISCLAIMER}"


def _kira_artis_itiraz_ihtarname() -> DocumentLayout:
    return DocumentLayout(
        pdf_title="Fahiş Kira Artışına İtiraz İhtarnamesi",
        footer=FOOTER_TEXT,
        paragraphs=[
            Paragraph([("{{ noter_ili }}", True), (" Nöbetçi Noterliğine", True)], align="center"),
            Paragraph([("İHTARNAME", True)], align="center"),
            Paragraph([("KEŞİDECİ (Kiracı): ", True), ("{{ kiraci_ad_soyad }}", False), ("{{ kiraci_tc_ibare }}", False)], align="left"),
            Paragraph([("Adres: ", True), ("{{ kiraci_adres }}", False)], align="left"),
            Paragraph([("MUHATAP (Kiraya Veren): ", True), ("{{ kiraya_veren_ad_soyad }}", False), ("{{ kiraya_veren_tc_ibare }}", False)], align="left"),
            Paragraph([("Adres: ", True), ("{{ kiraya_veren_adres }}", False)], align="left"),
            Paragraph([("KİRALANAN: ", True), ("{{ tasinmaz_adresi }}", False)], align="left"),
            Paragraph(
                [
                    ("KONU: ", True),
                    ("{{ kira_baslangic_tarihi }}", False),
                    (
                        " başlangıç tarihli kira sözleşmesine ilişkin olarak talep edilen kira artışının, "
                        "6098 sayılı Türk Borçlar Kanunu m. 344 uyarınca yasal sınırı aştığının ve bu sınırı "
                        "aşan kısmın kabul edilmediğinin bildirilmesidir.",
                        False,
                    ),
                ]
            ),
            Paragraph([("AÇIKLAMALAR:", True)], align="left"),
            Paragraph(
                [
                    ("1. Yukarıda adresi belirtilen taşınmazı, ", False),
                    ("{{ kira_baslangic_tarihi }}", False),
                    (" başlangıç tarihli kira sözleşmesi uyarınca kiracı sıfatıyla kullanmaktayım. Mevcut aylık kira bedeli ", False),
                    ("{{ mevcut_kira_tutari }}", True),
                    (" TL'dir.", True),
                ],
                first_line_indent=True,
            ),
            Paragraph(
                [
                    ("2. Tarafınızca yeni kira dönemi için aylık ", False),
                    ("{{ talep_edilen_kira_tutari }}", True),
                    (" TL", True),
                    (" kira bedeli talep edilmiştir. Bu talep, mevcut kira bedeline göre %", False),
                    ("{{ talep_artis_orani }}", False),
                    (" oranında bir artışa karşılık gelmektedir.", False),
                ],
                first_line_indent=True,
            ),
            Paragraph(
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
            ),
            Paragraph(
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
            ),
            Paragraph([("SONUÇ:", True)], align="left"),
            Paragraph(
                [
                    (
                        "İşbu ihtarnamenin bir suretinin muhataba tebliğini, bir suretinin dairenizde saklanmasını ve "
                        "tebliğ şerhini havi bir suretinin tarafıma verilmesini saygılarımla talep ederim.",
                        False,
                    )
                ],
                first_line_indent=True,
            ),
            Paragraph([("{{ belge_tarihi }}", False)], align="right"),
            Paragraph([("Keşideci", True)], align="right"),
            Paragraph([("{{ kiraci_ad_soyad }}", False)], align="right"),
            Paragraph([("İmza", False)], align="right"),
        ],
    )


def _kira_ihtarname_temerrut() -> DocumentLayout:
    return DocumentLayout(
        pdf_title="Kira Bedelinin Ödenmemesi Nedeniyle Temerrüt İhtarnamesi",
        footer=FOOTER_TEXT,
        paragraphs=[
            Paragraph([("{{ noter_ili }}", True), (" Nöbetçi Noterliğine", True)], align="center"),
            Paragraph([("İHTARNAME", True)], align="center"),
            Paragraph([("KEŞİDECİ (Kiraya Veren): ", True), ("{{ kiraya_veren_ad_soyad }}", False), ("{{ kiraya_veren_tc_ibare }}", False)], align="left"),
            Paragraph([("Adres: ", True), ("{{ kiraya_veren_adres }}", False)], align="left"),
            Paragraph([("MUHATAP (Kiracı): ", True), ("{{ kiraci_ad_soyad }}", False), ("{{ kiraci_tc_ibare }}", False)], align="left"),
            Paragraph([("Adres: ", True), ("{{ kiraci_adres }}", False)], align="left"),
            Paragraph([("KİRALANAN: ", True), ("{{ tasinmaz_adresi }}", False)], align="left"),
            Paragraph(
                [
                    ("KONU: ", True),
                    (
                        "Ödenmeyen kira bedellerinin 6098 sayılı Türk Borçlar Kanunu m. 315 uyarınca verilen süre "
                        "içinde ödenmesi, aksi halde kira sözleşmesinin feshedileceğinin ihtarıdır.",
                        False,
                    ),
                ]
            ),
            Paragraph([("AÇIKLAMALAR:", True)], align="left"),
            Paragraph(
                [
                    ("1. Yukarıda adresi belirtilen taşınmaz, ", False),
                    ("{{ kira_baslangic_tarihi }}", False),
                    (" başlangıç tarihli kira sözleşmesi ile tarafınıza kiralanmıştır. Aylık kira bedeli ", False),
                    ("{{ kira_tutari }}", True),
                    (" TL'dir.", True),
                ],
                first_line_indent=True,
            ),
            Paragraph(
                [
                    ("2. Kira sözleşmesi uyarınca ödenmesi gereken ", False),
                    ("{{ gecikilen_aylar }}", True),
                    (
                        " dönemlerine ait kira bedelleri, muaccel olmasına rağmen tarafınızca ödenmemiştir. "
                        "Ödenmeyen kira bedellerinin toplamı ",
                        False,
                    ),
                    ("{{ odenmeyen_toplam_tutar }}", True),
                    (" TL", True),
                    ("'dir.", False),
                ],
                first_line_indent=True,
            ),
            Paragraph(
                [
                    (
                        "3. 6098 sayılı Türk Borçlar Kanunu'nun 315. maddesi uyarınca, kiracı kiralananın tesliminden "
                        "sonra muaccel olan kira bedelini ödeme borcunu ifa etmezse kiraya veren, kiracıya yazılı "
                        "olarak bir süre verip bu sürede de ifa etmeme durumunda sözleşmeyi feshedeceğini bildirebilir. "
                        "Konut ve çatılı işyeri kiralarında bu süre en az otuz gündür ve yazılı bildirimin yapıldığı "
                        "tarihi izleyen günden itibaren işlemeye başlar.",
                        False,
                    ),
                ],
                first_line_indent=True,
            ),
            Paragraph(
                [
                    ("4. Açıklanan nedenlerle, ödenmeyen ", False),
                    ("{{ odenmeyen_toplam_tutar }}", True),
                    (" TL", True),
                    (" tutarındaki kira bedelini işbu ihtarnamenin tebliğini izleyen günden itibaren ", False),
                    ("{{ odeme_suresi_gun }}", True),
                    (" gün", True),
                    (
                        " içinde aşağıda belirtilen banka hesabına ödemenizi; bu süre içinde ödeme yapmamanız "
                        "halinde kira sözleşmesini feshedeceğimi ve tahliye için yasal yollara başvuracağımı ihtar ederim.",
                        False,
                    ),
                ],
                first_line_indent=True,
            ),
            Paragraph([("Ödeme Yapılacak Hesap (IBAN): ", True), ("{{ iban }}", False)], align="left"),
            Paragraph([("Hesap Sahibi: ", True), ("{{ kiraya_veren_ad_soyad }}", False)], align="left"),
            Paragraph([("SONUÇ:", True)], align="left"),
            Paragraph(
                [
                    (
                        "İşbu ihtarnamenin bir suretinin muhataba tebliğini, bir suretinin dairenizde saklanmasını ve "
                        "tebliğ şerhini havi bir suretinin tarafıma verilmesini saygılarımla talep ederim.",
                        False,
                    )
                ],
                first_line_indent=True,
            ),
            Paragraph([("{{ belge_tarihi }}", False)], align="right"),
            Paragraph([("Keşideci", True)], align="right"),
            Paragraph([("{{ kiraya_veren_ad_soyad }}", False)], align="right"),
            Paragraph([("İmza", False)], align="right"),
        ],
    )


_LAYOUTS = {
    "kira_artis_itiraz_ihtarname": _kira_artis_itiraz_ihtarname(),
    "kira_ihtarname_temerrut": _kira_ihtarname_temerrut(),
}


def get_layout(template_id: str) -> Optional[DocumentLayout]:
    """Layout for a template with a real renderer, or None if the template is still mocked."""
    return _LAYOUTS.get(template_id)


def layout_template_ids() -> List[str]:
    return list(_LAYOUTS)
