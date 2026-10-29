"""doc_service tests: real .docx rendering, template integrity and KVKK leakage checks.

Imports doc_service directly (no FastAPI app), so these run without network, Groq or
sentence-transformers.
"""

import re
import uuid
import zipfile

import pytest
from docx import Document
from docxtpl import DocxTemplate

from app.services import doc_service as doc_service_module
from app.services.doc_service import KIRA_ARTIS_TEMPLATE_ID, doc_service

UUID_DOCX_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.docx$")


def _kira_artis_case_params():
    return {
        "kira_baslangic_tarihi": "2022-09-01",
        "mevcut_kira_tutari": 12000,
        "talep_edilen_kira_tutari": 24000,
        "tufe_oran": 62.51,
        "noter_ili": "Ankara",
    }


def _kira_artis_pii():
    return {
        "kiraci_ad_soyad": "Tolga Yılmaz",
        "kiraci_tc": "19482910382",
        "kiraci_adres": "Ayrancı Mah. Güvenlik Cad. 24/5 Çankaya / ANKARA",
        "kiraya_veren_ad_soyad": "Hikmet Çetin",
        "kiraya_veren_tc": "38291048214",
        "kiraya_veren_adres": "Kızılay Mah. Atatürk Bulvarı 10/3 Çankaya / ANKARA",
        "tasinmaz_adresi": "Bahçelievler Mah. 7. Cadde 12/4 Çankaya / ANKARA",
    }


def _document_text(path) -> str:
    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs]
    for section in doc.sections:
        parts.extend(p.text for p in section.footer.paragraphs)
    return "\n".join(parts)


@pytest.fixture
def temp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(doc_service_module, "STORAGE_TEMP_DIR", tmp_path)
    return tmp_path


async def _generate(case_params, pii, template_id=KIRA_ARTIS_TEMPLATE_ID):
    template = doc_service.get_template(template_id)
    errors = doc_service.validate_fields(template, case_params, pii)
    assert not errors.has_errors, errors.to_message()
    return await doc_service.generate_documents(template_id, case_params, pii)


# ---------------------------------------------------------------------------
# Template integrity
# ---------------------------------------------------------------------------


def test_template_file_exists_for_kira_artis():
    assert doc_service.template_path(KIRA_ARTIS_TEMPLATE_ID).is_file()


def test_template_tags_are_not_split_across_runs():
    """docxtpl only replaces tags that sit inside one <w:t>; a split tag leaves '{{' behind."""
    with zipfile.ZipFile(doc_service.template_path(KIRA_ARTIS_TEMPLATE_ID)) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
    texts = re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", xml)
    assert any("{{" in t for t in texts)
    for text in texts:
        assert text.count("{{") == text.count("}}"), f"Split tag in run: {text!r}"
        assert text.count("{%") == text.count("%}"), f"Split block tag in run: {text!r}"


def test_template_variables_match_render_context():
    tpl = DocxTemplate(str(doc_service.template_path(KIRA_ARTIS_TEMPLATE_ID)))
    declared = tpl.get_undeclared_template_variables()
    context = doc_service.build_render_context(KIRA_ARTIS_TEMPLATE_ID, _kira_artis_case_params(), _kira_artis_pii())
    assert declared == set(context)


def test_template_listed_with_expected_fields():
    template = doc_service.get_template(KIRA_ARTIS_TEMPLATE_ID)
    case_names = {f.field_name for f in template.case_param_fields}
    pii_names = {f.field_name for f in template.pii_fields}
    assert case_names == {"kira_baslangic_tarihi", "mevcut_kira_tutari", "talep_edilen_kira_tutari", "tufe_oran", "noter_ili"}
    assert {"kiraci_ad_soyad", "kiraci_adres", "kiraya_veren_adres", "tasinmaz_adresi"} <= pii_names
    # Addresses are PII and must never sit in the LLM-facing case_params
    assert not any("adres" in name for name in case_names)


def test_existing_templates_unchanged():
    assert doc_service.get_template("kira_ihtarname_temerrut") is not None
    assert doc_service.get_template("tuketici_ayipli_mal_ihtarname") is not None


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_real_docx_replaces_all_fields(temp_storage):
    pii = _kira_artis_pii()
    file_id, docx_url, _, _ = await _generate(_kira_artis_case_params(), pii)

    docx_path = temp_storage / f"{file_id}.docx"
    assert docx_url.endswith(f"{file_id}.docx")
    text = _document_text(docx_path)

    assert "{{" not in text and "}}" not in text
    for value in pii.values():
        assert value in text
    assert "Ankara Nöbetçi Noterliğine" in text
    assert "01.09.2022" in text
    assert "12.000,00 TL" in text
    assert "24.000,00 TL" in text
    assert "%100,00" in text
    assert "avukatlık hizmeti vermez" in text
    assert not list(temp_storage.glob("*.tmp"))


@pytest.mark.asyncio
async def test_legal_ceiling_computed_from_user_rate(temp_storage):
    file_id, *_ = await _generate(_kira_artis_case_params(), _kira_artis_pii())
    text = _document_text(temp_storage / f"{file_id}.docx")
    # 12.000 x (1 + 62,51 / 100) = 19.501,20
    assert "%62,51" in text
    assert "19.501,20 TL" in text


@pytest.mark.asyncio
async def test_rate_is_not_hardcoded(temp_storage):
    case_params = _kira_artis_case_params()
    case_params["tufe_oran"] = "40"
    file_id, *_ = await _generate(case_params, _kira_artis_pii())
    text = _document_text(temp_storage / f"{file_id}.docx")
    assert "%40,00" in text
    assert "16.800,00 TL" in text
    assert "62,51" not in text


@pytest.mark.asyncio
async def test_turkish_and_xml_special_characters_survive(temp_storage):
    pii = _kira_artis_pii()
    pii["kiraya_veren_ad_soyad"] = "Çağlar & Oğulları <Şirketi> İşçi Ğüşıö"
    file_id, *_ = await _generate(_kira_artis_case_params(), pii)
    text = _document_text(temp_storage / f"{file_id}.docx")
    assert "Çağlar & Oğulları <Şirketi> İşçi Ğüşıö" in text
    assert "KEŞİDECİ" in text and "İHTARNAME" in text


@pytest.mark.asyncio
async def test_optional_tc_omitted_cleanly(temp_storage):
    pii = _kira_artis_pii()
    del pii["kiraci_tc"]
    del pii["kiraya_veren_tc"]
    file_id, *_ = await _generate(_kira_artis_case_params(), pii)
    text = _document_text(temp_storage / f"{file_id}.docx")
    assert "T.C. Kimlik No" not in text
    assert "None" not in text


@pytest.mark.asyncio
async def test_dropped_case_param_not_in_document(temp_storage):
    case_params = _kira_artis_case_params()
    case_params["llm_ek_alan"] = "gizli_deger_123"
    file_id, *_ = await _generate(case_params, _kira_artis_pii())
    assert "gizli_deger_123" not in _document_text(temp_storage / f"{file_id}.docx")


# ---------------------------------------------------------------------------
# KVKK: file names, mock files, logs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_file_names_are_random_and_pii_free(temp_storage):
    pii = _kira_artis_pii()
    file_id, docx_url, pdf_url, _ = await _generate(_kira_artis_case_params(), pii)

    uuid.UUID(file_id, version=4)
    names = [p.name for p in temp_storage.iterdir()]
    assert sorted(names) == sorted([f"{file_id}.docx", f"{file_id}.pdf"])
    assert UUID_DOCX_RE.match(f"{file_id}.docx")
    for value in pii.values():
        for token in value.split():
            if len(token) > 3:
                assert token not in docx_url and token not in pdf_url
                assert all(token not in name for name in names)


@pytest.mark.asyncio
async def test_mock_files_do_not_contain_pii(temp_storage):
    case_params = {
        "kira_tutari": 18000,
        "gecikilen_aylar": "Eylül-Ekim 2026",
        "odeme_suresi_gun": 30,
        "tasinmaz_adresi": "Kadıköy / İstanbul",
    }
    pii = {
        "kiraya_veren_ad_soyad": "Mehmet Yılmaz",
        "kiraya_veren_tc": "11111111111",
        "kiraci_ad_soyad": "Ali Demir",
        "iban": "TR120006100511123456789012",
    }
    file_id, *_ = await _generate(case_params, pii, template_id="kira_ihtarname_temerrut")
    for suffix in (".docx", ".pdf"):
        content = (temp_storage / f"{file_id}{suffix}").read_text(encoding="utf-8")
        assert "kira_ihtarname_temerrut" in content
        for value in list(pii.values()) + ["Kadıköy", "18000"]:
            assert value not in content


@pytest.mark.asyncio
async def test_real_template_pdf_is_mock_without_pii(temp_storage):
    pii = _kira_artis_pii()
    file_id, *_ = await _generate(_kira_artis_case_params(), pii)
    content = (temp_storage / f"{file_id}.pdf").read_text(encoding="utf-8")
    for value in pii.values():
        assert value not in content


@pytest.mark.asyncio
async def test_generation_logs_no_pii(temp_storage, caplog):
    pii = _kira_artis_pii()
    with caplog.at_level("DEBUG"):
        await _generate(_kira_artis_case_params(), pii)
    for value in pii.values():
        assert value not in caplog.text


@pytest.mark.asyncio
async def test_missing_template_file_falls_back_to_mock(temp_storage, tmp_path, monkeypatch):
    empty_dir = tmp_path / "no_templates"
    empty_dir.mkdir()
    monkeypatch.setattr(doc_service_module.settings, "TEMPLATES_DIR", str(empty_dir))
    pii = _kira_artis_pii()
    file_id, *_ = await _generate(_kira_artis_case_params(), pii)
    content = (temp_storage / f"{file_id}.docx").read_text(encoding="utf-8")
    assert KIRA_ARTIS_TEMPLATE_ID in content
    assert pii["kiraci_ad_soyad"] not in content


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate(case_params, pii):
    template = doc_service.get_template(KIRA_ARTIS_TEMPLATE_ID)
    return doc_service.validate_fields(template, case_params, pii)


def test_valid_payload_passes():
    assert not _validate(_kira_artis_case_params(), _kira_artis_pii()).has_errors


@pytest.mark.parametrize("field", ["tufe_oran", "mevcut_kira_tutari", "noter_ili", "kira_baslangic_tarihi"])
def test_missing_required_case_param(field):
    case_params = _kira_artis_case_params()
    del case_params[field]
    errors = _validate(case_params, _kira_artis_pii())
    assert errors.missing == [field]


@pytest.mark.parametrize("field", ["kiraci_adres", "kiraya_veren_adres", "tasinmaz_adresi", "kiraci_ad_soyad"])
def test_missing_required_pii(field):
    pii = _kira_artis_pii()
    del pii[field]
    errors = _validate(_kira_artis_case_params(), pii)
    assert errors.missing == [field]


@pytest.mark.parametrize("talep", [12000, 15000, 19501.20, "19501.2"])
def test_request_within_legal_ceiling_rejected(talep):
    case_params = _kira_artis_case_params()
    case_params["talep_edilen_kira_tutari"] = talep
    errors = _validate(case_params, _kira_artis_pii())
    assert errors.invalid == ["talep_edilen_kira_tutari"]
    message = errors.to_message()
    assert "talep_edilen_kira_tutari" in message
    assert str(talep) not in message
    assert "19501" not in message and "19.501" not in message


def test_request_one_kurus_over_ceiling_accepted():
    case_params = _kira_artis_case_params()
    case_params["talep_edilen_kira_tutari"] = 19501.21
    assert not _validate(case_params, _kira_artis_pii()).has_errors


@pytest.mark.parametrize("oran", [-1, 200.01, 6251, "nan", "inf"])
def test_tufe_rate_out_of_range_rejected(oran):
    case_params = _kira_artis_case_params()
    case_params["tufe_oran"] = oran
    errors = _validate(case_params, _kira_artis_pii())
    assert errors.invalid == ["tufe_oran"]
    assert str(oran) not in errors.to_message()


@pytest.mark.parametrize("mevcut", [0, -500])
def test_non_positive_current_rent_rejected(mevcut):
    case_params = _kira_artis_case_params()
    case_params["mevcut_kira_tutari"] = mevcut
    errors = _validate(case_params, _kira_artis_pii())
    assert errors.invalid == ["mevcut_kira_tutari"]


def test_cross_field_rule_skipped_when_field_already_invalid():
    case_params = _kira_artis_case_params()
    case_params["talep_edilen_kira_tutari"] = "yirmi dört bin"
    errors = _validate(case_params, _kira_artis_pii())
    assert errors.invalid == ["talep_edilen_kira_tutari"]


def test_invalid_tc_rejected_without_value_in_message():
    pii = _kira_artis_pii()
    pii["kiraci_tc"] = "1948291038"
    errors = _validate(_kira_artis_case_params(), pii)
    assert errors.invalid == ["kiraci_tc"]
    assert "1948291038" not in errors.to_message()
