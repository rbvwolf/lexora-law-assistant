"""Integration and unit tests for RAG retrieval service and statutory article querying."""

import pytest

from app.core.config import format_passage, format_query, settings
from app.schemas.chat import Citation
from app.services.rag_service import rag_service


def test_prefix_helper_functions():
    """Verify format_passage and format_query add prefixes for e5 and leave other models unchanged."""
    # E5 models require 'passage: ' and 'query: ' prefixes
    assert format_passage("Örnek kanun metni", model_name="intfloat/multilingual-e5-base") == "passage: Örnek kanun metni"
    assert format_query("Örnek kullanıcı sorusu", model_name="intfloat/multilingual-e5-base") == "query: Örnek kullanıcı sorusu"
    assert format_passage("Metin", model_name="multilingual-e5-small") == "passage: Metin"

    # MPNet / other models should NOT be prefixed
    mpnet_model = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    assert format_passage("Örnek metin", model_name=mpnet_model) == "Örnek metin"
    assert format_query("Örnek soru", model_name=mpnet_model) == "Örnek soru"


def test_empty_query_returns_empty_list():
    """Verify empty, blank, or invalid queries return an empty citation list without errors."""
    assert rag_service.retrieve_articles("") == []
    assert rag_service.retrieve_articles("   ") == []
    assert rag_service.retrieve_articles(None) == []  # type: ignore[arg-type]


def test_top_k_edge_cases():
    """Verify edge case values for top_k parameter (zero, negative, excessively large)."""
    # Non-positive top_k should return empty list gracefully without throwing ChromaDB TypeError
    assert rag_service.retrieve_articles("kira sözleşmesi", top_k=0) == []
    assert rag_service.retrieve_articles("kira sözleşmesi", top_k=-1) == []

    # Large top_k should not crash, clamped to available total docs
    citations = rag_service.retrieve_articles("kira", top_k=500)
    assert len(citations) <= 87
    assert len(citations) > 0


def test_special_characters_and_punctuation():
    """Verify retrieval handles complex Turkish punctuation, quotes, and symbols without crashing."""
    tr_query = "Kiracı 'tahliye taahhütnamesi' imzaladı; 15 gün içinde çıkmazsa ne yapılabilir? (TBK m.352/1)"
    citations = rag_service.retrieve_articles(tr_query, top_k=3)
    assert len(citations) == 3
    for c in citations:
        assert isinstance(c, Citation)

    # SQL/Prompt-injection-like characters should be embedded harmlessly
    injection_query = "'; DROP TABLE articles; -- SELECT * FROM users WHERE 1=1"
    injection_res = rag_service.retrieve_articles(injection_query, top_k=2)
    assert len(injection_res) <= 2


def test_unknown_domain_filter_returns_empty():
    """Verify querying with a non-existent domain filter returns empty list gracefully."""
    citations = rag_service.retrieve_articles("hırsızlık suçu", top_k=5, domain_filter="ceza_hukuku")
    assert citations == []


def test_whitespace_domain_filter_ignored():
    """Verify whitespace or empty string domain filter does not crash and behaves as no filter."""
    citations = rag_service.retrieve_articles("kira bedeli", top_k=3, domain_filter="   ")
    assert len(citations) == 3


def test_long_narrative_query():
    """Verify that a long, multi-sentence user scenario is handled properly and returns top matches."""
    narrative_query = (
        "Merhaba, yaklaşık 3 yıldır aynı dairede kiracı olarak oturuyorum. Ev sahibim geçen ay arayıp "
        "oğlunun evleneceğini ve acilen evi boşaltmam gerektiğini söyledi. Ancak bana herhangi bir yazılı "
        "bildirim yapmadı, sadece sözlü olarak söyledi. Kira bedelimi her ay düzenli olarak bankadan IBAN'a "
        "yatırıyorum. Ev sahibi beni bu şekilde hemen evden çıkarabilir mi, yasal haklarım ve sürelerim nelerdir?"
    )
    citations = rag_service.retrieve_articles(narrative_query, top_k=5)
    assert len(citations) == 5
    article_ids = [c.article_id for c in citations]
    # Should retrieve eviction-related articles like TBK-350 (Gereksinim sebebiyle tahliye) or TBK-352
    assert any(art in article_ids for art in ["TBK-350", "TBK-351", "TBK-352", "TBK-347"]), (
        f"Expected eviction ground articles in results, got: {article_ids}"
    )


def test_pii_masked_query_retrieval():
    """Verify that user queries with masked PII placeholders (e.g. [ISIM], [TC_NO]) retrieve correct legal articles."""
    masked_query = "Kiracım [ISIM] kirayı ödemiyor, [TARIH] tarihinde evden nasıl tahliye ederim?"
    citations = rag_service.retrieve_articles(masked_query, top_k=5)
    assert len(citations) > 0
    article_ids = [c.article_id for c in citations]
    assert "TBK-315" in article_ids, f"Expected TBK-315 in top-5 for masked query, got: {article_ids}"


def test_rental_question_retrieves_tbk_315():
    """Verify that a rental default/eviction question retrieves TBK-315 in the top-5 results."""
    query = "Kiracı kira bedelini ödemezse tahliye süreci nasıl işler?"
    citations = rag_service.retrieve_articles(query, top_k=5)

    assert len(citations) > 0
    article_ids = [c.article_id for c in citations]
    assert "TBK-315" in article_ids, f"Expected 'TBK-315' in top-5 results, got: {article_ids}"

    # Verify citation object adheres strictly to Citation schema
    tbk_315_citation = next(c for c in citations if c.article_id == "TBK-315")
    assert isinstance(tbk_315_citation, Citation)
    assert "Türk Borçlar Kanunu" in tbk_315_citation.law_name
    assert "temerrüt" in tbk_315_citation.text_snippet.lower() or "ödeme" in tbk_315_citation.text_snippet.lower()


def test_consumer_question_retrieves_tkhk_11():
    """Verify that a defective goods question retrieves TKHK-11 (optional consumer rights) in top-5."""
    query = "Ayıplı malda tüketicinin seçimlik hakları nelerdir?"
    citations = rag_service.retrieve_articles(query, top_k=5)

    assert len(citations) > 0
    article_ids = [c.article_id for c in citations]
    assert "TKHK-11" in article_ids, f"Expected 'TKHK-11' in top-5 results, got: {article_ids}"

    # Verify citation schema contract
    tkhk_11_citation = next(c for c in citations if c.article_id == "TKHK-11")
    assert isinstance(tkhk_11_citation, Citation)
    assert "Tüketicinin Korunması" in tkhk_11_citation.law_name
    assert "seçimlik" in tkhk_11_citation.text_snippet.lower() or "ayıp" in tkhk_11_citation.text_snippet.lower()


def test_domain_filter_restricts_results():
    """Verify domain_filter properly restricts retrieved articles to the given legal domain."""
    query = "Fesih bildirimi ve süreler"
    # Filter only labor law
    is_citations = rag_service.retrieve_articles(query, top_k=5, domain_filter="is_hukuku")
    for c in is_citations:
        assert c.article_id.startswith("IK-"), f"Expected IK- article, got: {c.article_id}"

    # Filter only rental law
    kira_citations = rag_service.retrieve_articles(query, top_k=5, domain_filter="kira_hukuku")
    for c in kira_citations:
        assert c.article_id.startswith("TBK-"), f"Expected TBK- article, got: {c.article_id}"


@pytest.mark.asyncio
async def test_async_retrieve_citations_compatibility():
    """Verify async retrieve_citations endpoint works and returns valid Citation models."""
    query = "Kiracı kirayı ödemezse ne olur?"
    citations = await rag_service.retrieve_citations(query, top_k=3)
    assert len(citations) <= 3
    for c in citations:
        assert isinstance(c, Citation)
        assert c.article_id
        assert c.law_name
        assert c.text_snippet
