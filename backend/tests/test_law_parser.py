"""Unit tests for Turkish statutory text parser and generated law JSONs."""

import json
from pathlib import Path

import pytest
from scripts.parse_raw_laws import (
    LAW_REGISTRY,
    clean_article_body,
    clean_title_part,
    format_article_title,
    is_heading_line,
    parse_law_content,
)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def test_heading_detection_and_cleaning():
    """Test heading regex detection and footnote/prefix stripping."""
    # Part/Chapter markers
    assert is_heading_line("BİRİNCİ AYIRIM")
    assert is_heading_line("İKİNCİ BÖLÜM")
    assert is_heading_line("Genel Hükümler")

    # Prefixes and footnotes
    assert is_heading_line("A. Tanımı")
    assert is_heading_line("III. Kira ilişkisinin devri [2]")
    assert is_heading_line("2. Kiralananın sözleşmenin bitiminden önce geri verilmesi2")
    assert is_heading_line("a. Şekil")
    assert is_heading_line("Ayıplı mal")
    assert is_heading_line("Süreli fesih")
    assert is_heading_line("I- Sağlık sebepleri")

    # Non-headings (body paragraphs that end with punctuation)
    assert not is_heading_line("Kiracı, kira bedelini ödemekle yükümlüdür.")
    assert not is_heading_line("(1) Ayıplı mal, tüketiciye teslimi anında...")
    assert not is_heading_line(
        "1. Borçlunun içinde bulunduğu durumdan veya tutumundan süre verilmesinin etkisiz olacağı anlaşılıyorsa."
    )

    # Cleaning
    assert clean_title_part("III. Kira ilişkisinin devri [2]") == "Kira ilişkisinin devri"
    assert clean_title_part("2. Kiralananın sözleşmenin bitiminden önce geri verilmesi2") == (
        "Kiralananın sözleşmenin bitiminden önce geri verilmesi"
    )
    assert clean_title_part("II. Belirlenmesi2[3][4]") == "Belirlenmesi"
    assert clean_title_part("A. Tanımı") == "Tanımı"
    assert clean_title_part("I- Sağlık sebepleri") == "Sağlık sebepleri"


def test_format_article_title():
    """Test hierarchical and generic title formatting."""
    # Simple title
    assert format_article_title(["B. Kira süresi"]) == "Kira süresi"

    # Filter division marker
    assert format_article_title(["BİRİNCİ AYIRIM", "Genel Hükümler", "A. Tanımı"]) == "Tanımı"

    # Generic title combined with parent
    headings = ["Kiralananın kullanılmaması", "1. Genel olarak"]
    assert format_article_title(headings) == "Kiralananın kullanılmaması - Genel olarak"

    headings_temerrut = ["Temerrüt faizi", "a. Genel olarak"]
    assert format_article_title(headings_temerrut) == "Temerrüt faizi - Genel olarak"


def test_clean_article_body():
    """Test whitespace, paragraph, and footnote normalization."""
    raw = "   Paragraph one sentence.[6]  \n\n\n   Paragraph two sentence.[7]  \n   More of paragraph two. "
    cleaned = clean_article_body(raw)
    assert cleaned == "Paragraph one sentence.\n\nParagraph two sentence. More of paragraph two."
    assert "[6]" not in cleaned
    assert "[7]" not in cleaned


def test_parse_law_content_synthetic():
    """Test parsing a synthetic Turkish statutory text."""
    sample = (
        "BİRİNCİ BÖLÜM\n"
        "Genel Hükümler\n\n"
        "A. Tanım\n"
        "MADDE 1- Bu kanunun amacı tüketicinin sağlığını korumaktır.\n\n"
        "Kanun kamu yararınadır.\n\n"
        "B. Kapsam\n"
        "Madde 2 - (1) Bu Kanun, her türlü tüketici işlemini kapsar.\n"
    )
    articles = parse_law_content(
        content=sample,
        law_name="Örnek Kanun",
        article_prefix="ORN",
        domain="ornek_hukuk",
    )
    assert len(articles) == 2
    assert articles[0].article_id == "ORN-1"
    assert articles[0].article_no == 1
    assert articles[0].title == "Tanım"
    assert articles[0].domain == "ornek_hukuk"
    assert "Bu kanunun amacı" in articles[0].text
    assert not articles[0].text.startswith("MADDE")

    assert articles[1].article_id == "ORN-2"
    assert articles[1].article_no == 2
    assert articles[1].title == "Kapsam"
    assert articles[1].text.startswith("(1) Bu Kanun")


def test_generated_tbk_kira_json(repo_root: Path):
    """Validate data/laws/tbk_kira.json article completeness and schema contracts."""
    json_path = repo_root / "data" / "laws" / "tbk_kira.json"
    assert json_path.exists(), f"File missing: {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # Exactly 58 articles (Madde 299 to 356)
    assert len(articles) == 58

    expected_article_nos = list(range(299, 357))
    actual_article_nos = [a["article_no"] for a in articles]
    assert actual_article_nos == expected_article_nos

    for art in articles:
        assert art["article_id"] == f"TBK-{art['article_no']}"
        assert art["law"] == "6098 Sayılı Türk Borçlar Kanunu"
        assert isinstance(art["article_no"], int)
        assert art["domain"] == "kira_hukuku"
        assert len(art["title"].strip()) > 0
        assert len(art["text"].strip()) > 0
        assert not art["text"].startswith("MADDE")

    tbk_315 = next(a for a in articles if a["article_no"] == 315)
    assert tbk_315["title"] == "Kiracının temerrüdü"
    assert "muaccel olan kira bedelini" in tbk_315["text"]

    tbk_344 = next(a for a in articles if a["article_no"] == 344)
    assert tbk_344["title"] == "Belirlenmesi"
    assert "tüketici fiyat endeksindeki" in tbk_344["text"]


def test_generated_tkhk_tuketici_json(repo_root: Path):
    """Validate data/laws/tkhk_tuketici.json article completeness and schema contracts."""
    json_path = repo_root / "data" / "laws" / "tkhk_tuketici.json"
    assert json_path.exists(), f"File missing: {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # Exactly 9 articles (Madde 8 to 16)
    assert len(articles) == 9

    expected_article_nos = list(range(8, 17))
    actual_article_nos = [a["article_no"] for a in articles]
    assert actual_article_nos == expected_article_nos

    for art in articles:
        assert art["article_id"] == f"TKHK-{art['article_no']}"
        assert art["law"] == "6502 Sayılı Tüketicinin Korunması Hakkında Kanun"
        assert isinstance(art["article_no"], int)
        assert art["domain"] == "tuketici_hukuku"
        assert len(art["title"].strip()) > 0
        assert len(art["text"].strip()) > 0
        assert not art["text"].startswith("MADDE")

    tkhk_8 = next(a for a in articles if a["article_no"] == 8)
    assert tkhk_8["title"] == "Ayıplı mal"
    assert "örnek ya da modele uygun olmaması" in tkhk_8["text"]

    tkhk_11 = next(a for a in articles if a["article_no"] == 11)
    assert tkhk_11["title"] == "Tüketicinin seçimlik hakları"
    assert "seçimlik haklarından birini kullanabilir" in tkhk_11["text"]


def test_generated_tbk_temerrut_json(repo_root: Path):
    """Validate data/laws/tbk_temerrut.json article completeness and schema contracts."""
    json_path = repo_root / "data" / "laws" / "tbk_temerrut.json"
    assert json_path.exists(), f"File missing: {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # Exactly 10 articles (Madde 117 to 126)
    assert len(articles) == 10

    expected_article_nos = list(range(117, 127))
    actual_article_nos = [a["article_no"] for a in articles]
    assert actual_article_nos == expected_article_nos

    for art in articles:
        assert art["article_id"] == f"TBK-{art['article_no']}"
        assert art["law"] == "6098 Sayılı Türk Borçlar Kanunu"
        assert isinstance(art["article_no"], int)
        assert art["domain"] == "borclar_genel"
        assert len(art["title"].strip()) > 0
        assert len(art["text"].strip()) > 0
        assert not art["text"].startswith("MADDE")

    tbk_117 = next(a for a in articles if a["article_no"] == 117)
    assert tbk_117["title"] == "Koşulları"
    assert "Muaccel bir borcun borçlusu, alacaklının ihtarıyla temerrüde düşer" in tbk_117["text"]

    tbk_120 = next(a for a in articles if a["article_no"] == 120)
    assert tbk_120["title"] == "Temerrüt faizi - Genel olarak"
    assert "yıllık temerrüt faizi oranı" in tbk_120["text"]


def test_generated_ik_is_json(repo_root: Path):
    """Validate data/laws/ik_is.json article completeness and schema contracts."""
    json_path = repo_root / "data" / "laws" / "ik_is.json"
    assert json_path.exists(), f"File missing: {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # Exactly 10 articles (Madde 17 to 26)
    assert len(articles) == 10

    expected_article_nos = list(range(17, 27))
    actual_article_nos = [a["article_no"] for a in articles]
    assert actual_article_nos == expected_article_nos

    for art in articles:
        assert art["article_id"] == f"IK-{art['article_no']}"
        assert art["law"] == "4857 Sayılı İş Kanunu"
        assert isinstance(art["article_no"], int)
        assert art["domain"] == "is_hukuku"
        assert len(art["title"].strip()) > 0
        assert len(art["text"].strip()) > 0
        assert not art["text"].startswith("MADDE")
        assert not art["text"].startswith("Madde")
        assert "[6]" not in art["text"]
        assert "[7]" not in art["text"]

    ik_17 = next(a for a in articles if a["article_no"] == 17)
    assert ik_17["title"] == "Süreli fesih"
    assert "Belirsiz süreli iş sözleşmelerinin feshinden önce" in ik_17["text"]

    ik_24 = next(a for a in articles if a["article_no"] == 24)
    assert ik_24["title"] == "İşçinin haklı nedenle derhal fesih hakkı"
    assert "Ahlak ve iyiniyet kurallarına uymayan haller" in ik_24["text"]


def test_total_law_corpus_completeness(repo_root: Path):
    """Verify that all 4 laws combined yield exactly 87 valid articles."""
    total_count = 0
    law_dir = repo_root / "data" / "laws"
    expected_files = {
        "tbk_kira.json": 58,
        "tkhk_tuketici.json": 9,
        "tbk_temerrut.json": 10,
        "ik_is.json": 10,
    }

    for fname, exp_count in expected_files.items():
        file_path = law_dir / fname
        assert file_path.exists()
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) == exp_count
            total_count += len(data)

    assert total_count == 87, f"Expected 87 total articles across corpus, got {total_count}"
