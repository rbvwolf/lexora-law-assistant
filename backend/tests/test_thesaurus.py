"""Unit tests for LegalThesaurus colloquial-to-statutory vocabulary expansion."""

from app.core.thesaurus import LegalThesaurus, legal_thesaurus


def test_thesaurus_empty_and_blank_query():
    """Verify that empty, none, or whitespace queries return empty string without error."""
    assert legal_thesaurus.expand_query("") == ""
    assert legal_thesaurus.expand_query("   ") == ""
    assert legal_thesaurus.expand_query(None) == ""  # type: ignore[arg-type]


def test_thesaurus_query_without_matching_terms():
    """Verify that queries without colloquial gaps are returned unaltered."""
    query = "Kiracı sözleşmeyi süresinde feshetti mi?"
    assert legal_thesaurus.expand_query(query) == query


def test_thesaurus_depozito_expansion():
    """Verify that depozito variations expand with güvence bedeli without hardcoding article numbers."""
    queries = [
        "Ev sahibi 3 aylık depozito istiyor",
        "Depozitomu ne zaman geri alabilirim?",
        "Depozitosu bankaya mı yatırılmalı?",
    ]
    for q in queries:
        expanded = legal_thesaurus.expand_query(q)
        assert "güvence bedeli" in expanded
        # Must NOT hardcode law article IDs
        assert "TBK" not in expanded
        assert "342" not in expanded


def test_thesaurus_kinship_expansion():
    """Verify kinship terms (oğlum, kızım, annem, babam) expand to statutory altsoyu/üstsoyu."""
    assert "altsoyu" in legal_thesaurus.expand_query("Oğlum evleneceği için evi boşaltmanızı istiyorum.")
    assert "altsoyu" in legal_thesaurus.expand_query("Kızımın konut ihtiyacı sebebiyle tahliye davası açabilir miyim?")
    assert "üstsoyu" in legal_thesaurus.expand_query("Annemin oturması için kiracıyı çıkarabilir miyim?")
    assert "üstsoyu" in legal_thesaurus.expand_query("Babamın sağlık durumu nedeniyle daireye ihtiyacımız var.")


def test_thesaurus_labor_salary_expansion():
    """Verify colloquial salary terms (maaşım, fazla mesai) expand to statutory ücret."""
    expanded = legal_thesaurus.expand_query("İşverenim 2 aydır maaşımı ve fazla mesaimi ödemiyor.")
    assert "ücret" in expanded
    assert "fazla çalışma ücreti" in expanded


def test_thesaurus_consumer_defective_goods():
    """Verify defective item terms expand to canonical ayıplı mal."""
    assert "ayıplı mal" in legal_thesaurus.expand_query("Aldığım telefon bozuk çıktı.")
    assert "ayıplı mal" in legal_thesaurus.expand_query("Sıfır aldığım bilgisayar arızalı çıktı.")


def test_thesaurus_rent_increase_expansion():
    """Verify colloquial rent increase queries expand with TBK-344 statutory terms (TÜFE, kira bedeli)."""
    queries = [
        "Ev sahibim kiramı %100 artırmak istiyor, yasal mı?",
        "Kira artışı yasal sınırı neye göre belirlenir?",
        "Kira zammı için tavan oran nedir?",
        "Ev sahibi kiraya %80 zam yapabilir mi?",
    ]
    for q in queries:
        expanded = legal_thesaurus.expand_query(q)
        assert "tüketici fiyat endeksi tüfe" in expanded
        assert "kira bedelinin belirlenmesi" in expanded
        assert "TBK" not in expanded  # No hardcoded article IDs


def test_thesaurus_does_not_duplicate_existing_terms():
    """Verify that if the query already explicitly mentions the statutory term, it is not duplicated."""
    query = "Kiracının güvence bedeli sınırı nedir?"
    expanded = legal_thesaurus.expand_query(query)
    assert expanded == query
