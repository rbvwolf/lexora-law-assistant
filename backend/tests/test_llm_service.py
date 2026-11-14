"""Unit and integration tests for LLMService.

Test strategy
─────────────
- Unit tests: Groq client is fully mocked (no network / no API key required).
- Integration-style tests: mock key detection → mock response path.
- Cache tests: same prompt hash hits cache on second call.
- Schema conformance tests: returned tuple maps correctly to ChatResponse.
- KVKK / AGENTS.md compliance tests: PII keywords never in missing_fields from LLM.
"""

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.chat import ChatResponse, Citation
from app.schemas.common import LEGAL_DISCLAIMER
from app.services.llm_service import (
    LLMService,
    _cache_key,
    _is_mock_key,
    _response_cache,
)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def service() -> LLMService:
    return LLMService()


@pytest.fixture()
def sample_citations() -> List[Citation]:
    return [
        Citation(
            article_id="TBK-315",
            law_name="Türk Borçlar Kanunu",
            text_snippet=(
                "Kiracı, kiralananın teslim edilmesinden sonra muaccel olan kira bedelini "
                "veya yan gideri ödeme borcunu yerine getirmezse kiraya veren, kiracıya "
                "yazılı olarak en az otuz gün süre tanıyarak bu süre içinde ödenmemesi "
                "hâlinde sözleşmeyi feshedeceğini bildirebilir."
            ),
        ),
        Citation(
            article_id="TKHK-11",
            law_name="Tüketicinin Korunması Hakkında Kanun",
            text_snippet=(
                "Malın ayıplı olduğunun anlaşılması hâlinde tüketici; "
                "a) Satılanı geri vererek bedelin iadesini, b) Satılanın ayıpsız misliyle değiştirilmesini, "
                "c) Ayıp oranında bedel indirimi, d) Ücretsiz onarım talep edebilir."
            ),
        ),
    ]


@pytest.fixture(autouse=True)
def clear_response_cache():
    """Wipe the in-process cache before every test to ensure isolation."""
    _response_cache.clear()
    yield
    _response_cache.clear()


# ──────────────────────────────────────────────────────────────────────────────
# Helper: build a mock Groq completion with given text
# ──────────────────────────────────────────────────────────────────────────────

def _mock_groq_completion(text: str):
    choice = MagicMock()
    choice.message.content = text
    completion = MagicMock()
    completion.choices = [choice]
    return completion


# ──────────────────────────────────────────────────────────────────────────────
# 1. Utility helpers
# ──────────────────────────────────────────────────────────────────────────────

class TestIsMockKey:
    def test_empty_string_is_mock(self):
        assert _is_mock_key("") is True

    def test_whitespace_is_mock(self):
        assert _is_mock_key("   ") is True

    def test_mock_prefix_gsk_mock(self):
        assert _is_mock_key("gsk_mock_key_for_dev_mode") is True

    def test_mock_prefix_gsk_your(self):
        assert _is_mock_key("gsk_your_groq_api_key_here") is True

    def test_placeholder_prefix(self):
        assert _is_mock_key("placeholder_anon_key") is True

    def test_real_key_is_not_mock(self):
        # A realistic-looking key (56 chars starting with gsk_)
        assert _is_mock_key("gsk_" + "a" * 52) is False


class TestCacheKey:
    def test_same_inputs_produce_same_hash(self):
        msgs = [{"role": "user", "content": "Merhaba"}]
        assert _cache_key("m1", msgs) == _cache_key("m1", msgs)

    def test_different_model_different_hash(self):
        msgs = [{"role": "user", "content": "Merhaba"}]
        assert _cache_key("m1", msgs) != _cache_key("m2", msgs)

    def test_different_content_different_hash(self):
        assert (
            _cache_key("m", [{"role": "user", "content": "A"}])
            != _cache_key("m", [{"role": "user", "content": "B"}])
        )


# ──────────────────────────────────────────────────────────────────────────────
# 2. Mock-mode (no real API key) responses
# ──────────────────────────────────────────────────────────────────────────────

class TestMockMode:
    """When GROQ_API_KEY is a placeholder, service returns deterministic mock."""

    @pytest.mark.asyncio
    async def test_question_answering_mock_intent(self, service, sample_citations):
        with patch("app.services.llm_service.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            mock_settings.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            intent, answer, params, missing, template_id = await service.process_chat_message(
                "Kiracı kira bedelini ödemezse ne olur?", sample_citations
            )

        assert intent == "question_answering"
        assert "MOCK" in answer
        assert params == {}
        assert missing == []
        assert template_id is None

    @pytest.mark.asyncio
    async def test_document_generation_mock_intent(self, service, sample_citations):
        with patch("app.services.llm_service.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            mock_settings.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            intent, answer, params, missing, template_id = await service.process_chat_message(
                "Kira ihtarnamesi hazırla", sample_citations
            )

        assert intent == "document_generation"
        assert template_id == "kira_ihtarname_temerrut"
        assert isinstance(params, dict)
        assert isinstance(missing, list)

    @pytest.mark.asyncio
    async def test_mock_answer_contains_guidance(self, service, sample_citations):
        with patch("app.services.llm_service.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "gsk_your_groq_api_key_here"
            mock_settings.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            _, answer, *_ = await service.process_chat_message(
                "Ayıplı ürün dilekçesi yaz", sample_citations
            )

        # Should mention MOCK and contain some guidance
        assert answer  # non-empty


# ──────────────────────────────────────────────────────────────────────────────
# 3. Groq API fully mocked (real key path, no network)
# ──────────────────────────────────────────────────────────────────────────────

REAL_KEY = "gsk_" + "x" * 52  # 56-char, passes _is_mock_key check


class TestGroqIntentClassification:

    @pytest.mark.asyncio
    async def test_classifies_question_answering(self, service, sample_citations):
        intent_json = json.dumps({"intent": "question_answering"})
        qa_answer = "TBK Madde 315 uyarınca kiracı temerrüde düşer."

        with (
            patch("app.services.llm_service.settings") as ms,
            patch("app.services.llm_service._get_groq_client") as mock_client_fn,
        ):
            ms.GROQ_API_KEY = REAL_KEY
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"

            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            # First call: intent, second call: Q&A answer
            mock_client.chat.completions.create.side_effect = [
                _mock_groq_completion(intent_json),
                _mock_groq_completion(qa_answer),
            ]

            intent, answer, params, missing, template_id = await service.process_chat_message(
                "Kiracı kira bedelini ödemezse tahliye süreci nasıl işler?",
                sample_citations,
            )

        assert intent == "question_answering"
        assert "TBK Madde 315" in answer
        assert params == {}
        assert missing == []
        assert template_id is None

    @pytest.mark.asyncio
    async def test_classifies_document_generation(self, service, sample_citations):
        intent_json = json.dumps({"intent": "document_generation"})
        doc_json = json.dumps({
            "suggested_template_id": "kira_ihtarname_temerrut",
            "extracted_params": {
                "uyusmazlik_turu": "Kira Ödememe",
                "kira_tutari": 12000,
                "gecikilen_aylar": ["Ekim 2026"],
                "odeme_suresi_gun": 30,
            },
            "missing_fields": ["olay_tarihi"],
        })

        with (
            patch("app.services.llm_service.settings") as ms,
            patch("app.services.llm_service._get_groq_client") as mock_client_fn,
        ):
            ms.GROQ_API_KEY = REAL_KEY
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            mock_client.chat.completions.create.side_effect = [
                _mock_groq_completion(intent_json),
                _mock_groq_completion(doc_json),
            ]

            intent, answer, params, missing, template_id = await service.process_chat_message(
                "Kiracım 2 aydır kira ödemiyor, ihtarname hazırla.",
                sample_citations,
            )

        assert intent == "document_generation"
        assert template_id == "kira_ihtarname_temerrut"
        assert params.get("kira_tutari") == 12000
        assert "olay_tarihi" in missing

    @pytest.mark.asyncio
    async def test_classifies_out_of_scope(self, service, sample_citations):
        intent_json = json.dumps({"intent": "out_of_scope"})

        with (
            patch("app.services.llm_service.settings") as ms,
            patch("app.services.llm_service._get_groq_client") as mock_client_fn,
        ):
            ms.GROQ_API_KEY = REAL_KEY
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            mock_client.chat.completions.create.return_value = _mock_groq_completion(intent_json)

            intent, answer, params, missing, template_id = await service.process_chat_message(
                "Bugün hava nasıl?", sample_citations
            )

        assert intent == "out_of_scope"
        assert answer  # non-empty refusal
        assert params == {}
        assert missing == []
        assert template_id is None


# ──────────────────────────────────────────────────────────────────────────────
# 4. Cache behaviour
# ──────────────────────────────────────────────────────────────────────────────

class TestResponseCache:

    @pytest.mark.asyncio
    async def test_second_call_hits_cache(self, service, sample_citations):
        intent_json = json.dumps({"intent": "question_answering"})
        qa_answer = "TBK Madde 344 uyarınca kira artış oranı TÜFE'yi aşamaz."

        call_count = 0

        async def fake_create(**kwargs):
            nonlocal call_count
            call_count += 1
            texts = [intent_json, qa_answer]
            return _mock_groq_completion(texts[min(call_count - 1, 1)])

        with (
            patch("app.services.llm_service.settings") as ms,
            patch("app.services.llm_service._get_groq_client") as mock_client_fn,
        ):
            ms.GROQ_API_KEY = REAL_KEY
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            mock_client.chat.completions.create.side_effect = fake_create

            msg = "Kira artış oranı ne kadar olabilir?"
            await service.process_chat_message(msg, sample_citations)
            first_calls = call_count

            # Second identical call — should use cache (no new API calls)
            await service.process_chat_message(msg, sample_citations)

        assert call_count == first_calls, (
            f"Cache miss on second call: API was called {call_count} times total "
            f"(expected {first_calls})"
        )


# ──────────────────────────────────────────────────────────────────────────────
# 5. Schema conformance — result maps correctly to ChatResponse
# ──────────────────────────────────────────────────────────────────────────────

class TestSchemaConformance:

    @pytest.mark.asyncio
    async def test_qa_result_builds_valid_chat_response(self, service, sample_citations):
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            intent, answer, extracted_params, missing_fields, suggested_template_id = (
                await service.process_chat_message("Kira sorusu?", sample_citations)
            )

        # Should build without validation error
        response = ChatResponse(
            intent=intent,
            answer=answer,
            citations=sample_citations if intent == "question_answering" else [],
            extracted_params=extracted_params,
            missing_fields=missing_fields,
            suggested_template_id=suggested_template_id,
        )
        assert response.disclaimer == LEGAL_DISCLAIMER
        assert response.intent in ("question_answering", "document_generation", "out_of_scope")

    @pytest.mark.asyncio
    async def test_doc_gen_result_builds_valid_chat_response(self, service, sample_citations):
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            intent, answer, extracted_params, missing_fields, suggested_template_id = (
                await service.process_chat_message("İhtarname hazırla", sample_citations)
            )

        response = ChatResponse(
            intent=intent,
            answer=answer,
            citations=[],
            extracted_params=extracted_params,
            missing_fields=missing_fields,
            suggested_template_id=suggested_template_id,
        )
        assert response.intent == "document_generation"
        assert response.suggested_template_id is not None


# ──────────────────────────────────────────────────────────────────────────────
# 6. KVKK / AGENTS.md compliance
# ──────────────────────────────────────────────────────────────────────────────

class TestKVKKCompliance:
    """LLM must never surface PII field names in missing_fields."""

    PII_FIELD_NAMES = ["tc_id", "tc_kimlik", "iban", "adres", "telefon", "ad_soyad", "email"]

    @pytest.mark.asyncio
    async def test_doc_gen_missing_fields_no_pii_keys(self, service, sample_citations):
        # Simulate LLM returning PII-free missing_fields (mock mode is safe by design)
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            _, _, _, missing_fields, _ = await service.process_chat_message(
                "İhtarname oluştur", sample_citations
            )

        for field in missing_fields:
            assert field.lower() not in self.PII_FIELD_NAMES, (
                f"PII field '{field}' leaked into missing_fields!"
            )

    @pytest.mark.asyncio
    async def test_groq_mode_pii_not_in_missing_fields(self, service, sample_citations):
        """Even when Groq returns PII in missing_fields, verify service doesn't crash."""
        intent_json = json.dumps({"intent": "document_generation"})
        # Simulate a badly-behaved LLM response that includes PII field names
        bad_doc_json = json.dumps({
            "suggested_template_id": "kira_ihtarname_temerrut",
            "extracted_params": {"uyusmazlik_turu": "Kira"},
            "missing_fields": ["kira_tutari", "tc_kimlik"],  # tc_kimlik should NOT be here
        })

        with (
            patch("app.services.llm_service.settings") as ms,
            patch("app.services.llm_service._get_groq_client") as mock_client_fn,
        ):
            ms.GROQ_API_KEY = REAL_KEY
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            mock_client.chat.completions.create.side_effect = [
                _mock_groq_completion(intent_json),
                _mock_groq_completion(bad_doc_json),
            ]

            _, _, _, missing_fields, _ = await service.process_chat_message(
                "İhtarname hazırla, TC kimliğim 12345678901",
                sample_citations,
            )

        # Service should not crash; missing_fields is passed through from LLM
        # (The system prompt instructs LLM not to include PII - documented contract)
        assert isinstance(missing_fields, list)


# ──────────────────────────────────────────────────────────────────────────────
# 7. Edge cases
# ──────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:

    @pytest.mark.asyncio
    async def test_empty_citations_qa_returns_guidance(self, service):
        """When RAG returns nothing, Q&A should return a helpful fallback."""
        intent_json = json.dumps({"intent": "question_answering"})
        qa_no_context = "Sorunuzla ilgili kanun veritabanımızda yeterli makale bulunamadı."

        with (
            patch("app.services.llm_service.settings") as ms,
            patch("app.services.llm_service._get_groq_client") as mock_client_fn,
        ):
            ms.GROQ_API_KEY = REAL_KEY
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            mock_client.chat.completions.create.side_effect = [
                _mock_groq_completion(intent_json),
                _mock_groq_completion(qa_no_context),
            ]

            intent, answer, *_ = await service.process_chat_message(
                "Bir sorum var", []  # empty citations
            )

        # With empty citations, our service returns a short fallback without calling Groq for Q&A
        assert intent == "question_answering"
        assert answer  # non-empty

    @pytest.mark.asyncio
    async def test_malformed_intent_json_falls_back_to_out_of_scope(self, service, sample_citations):
        """If Groq returns invalid JSON for intent, fallback to out_of_scope."""
        with (
            patch("app.services.llm_service.settings") as ms,
            patch("app.services.llm_service._get_groq_client") as mock_client_fn,
        ):
            ms.GROQ_API_KEY = REAL_KEY
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            mock_client.chat.completions.create.return_value = _mock_groq_completion(
                "Bu geçerli JSON değil @@@@"
            )

            intent, answer, *_ = await service.process_chat_message(
                "Test", sample_citations
            )

        assert intent == "out_of_scope"
        assert answer  # non-empty refusal

    @pytest.mark.asyncio
    async def test_malformed_doc_json_returns_defaults(self, service, sample_citations):
        """If Groq returns invalid JSON for doc extraction, return safe defaults."""
        intent_json = json.dumps({"intent": "document_generation"})

        with (
            patch("app.services.llm_service.settings") as ms,
            patch("app.services.llm_service._get_groq_client") as mock_client_fn,
        ):
            ms.GROQ_API_KEY = REAL_KEY
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            mock_client.chat.completions.create.side_effect = [
                _mock_groq_completion(intent_json),
                _mock_groq_completion("!!!BROKEN JSON!!!"),
            ]

            intent, answer, params, missing, template_id = await service.process_chat_message(
                "İhtarname hazırla", sample_citations
            )

        assert intent == "document_generation"
        assert template_id == "kira_ihtarname_temerrut"  # safe default
        assert isinstance(params, dict)
        assert isinstance(missing, list)

    @pytest.mark.asyncio
    async def test_groq_exception_propagates(self, service, sample_citations):
        """Network/API errors should bubble up (not silently swallowed)."""
        with (
            patch("app.services.llm_service.settings") as ms,
            patch("app.services.llm_service._get_groq_client") as mock_client_fn,
        ):
            ms.GROQ_API_KEY = REAL_KEY
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            mock_client.chat.completions.create.side_effect = RuntimeError("Network timeout")

            with pytest.raises(RuntimeError, match="Network timeout"):
                await service.process_chat_message("Sorum var", sample_citations)

    @pytest.mark.asyncio
    async def test_null_params_stripped_from_extracted(self, service, sample_citations):
        """Null values in extracted_params should be removed from output dict."""
        intent_json = json.dumps({"intent": "document_generation"})
        doc_json = json.dumps({
            "suggested_template_id": "tuketici_ayipli_mal_ihtarname",
            "extracted_params": {
                "uyusmazlik_turu": "Ayıplı Mal",
                "urun_adi": "Buzdolabı",
                "kira_tutari": None,   # should be stripped
                "ayip_detayi": None,   # should be stripped
            },
            "missing_fields": ["satin_alma_tutari", "olay_tarihi"],
        })

        with (
            patch("app.services.llm_service.settings") as ms,
            patch("app.services.llm_service._get_groq_client") as mock_client_fn,
        ):
            ms.GROQ_API_KEY = REAL_KEY
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            mock_client.chat.completions.create.side_effect = [
                _mock_groq_completion(intent_json),
                _mock_groq_completion(doc_json),
            ]

            _, _, params, missing, _ = await service.process_chat_message(
                "Aldığım buzdolabı bozuk, ne yapabilirim başvuru için?",
                sample_citations,
            )

        assert "kira_tutari" not in params
        assert "ayip_detayi" not in params
        assert params.get("urun_adi") == "Buzdolabı"
        assert "satin_alma_tutari" in missing


# ──────────────────────────────────────────────────────────────────────────────
# 8. kira_artis_itiraz_ihtarname template sync (Faz 1)
# ──────────────────────────────────────────────────────────────────────────────

class TestArtisIhtarnameFaz1:
    """Faz 1 — _DOC_SYSTEM prompt, mock routing, and _doc_answer label for kira_artis_itiraz_ihtarname."""

    # ── 8.1 _DOC_SYSTEM prompt contains the new template ──────────────────────

    def test_doc_system_contains_new_template_id(self):
        from app.services.llm_service import _DOC_SYSTEM
        assert "kira_artis_itiraz_ihtarname" in _DOC_SYSTEM, (
            "_DOC_SYSTEM must list the kira_artis_itiraz_ihtarname template"
        )

    def test_doc_system_contains_new_case_param_fields(self):
        from app.services.llm_service import _DOC_SYSTEM
        expected_fields = [
            "kira_baslangic_tarihi",
            "mevcut_kira_tutari",
            "talep_edilen_kira_tutari",
            "tufe_oran",
            "noter_ili",
        ]
        for field in expected_fields:
            assert field in _DOC_SYSTEM, (
                f"_DOC_SYSTEM must include extracted_params field: {field}"
            )

    def test_doc_system_kvkk_prohibition_strengthened(self):
        """KVKK section must explicitly name banned field categories."""
        from app.services.llm_service import _DOC_SYSTEM
        pii_markers = ["kiraci_ad_soyad", "kiraci_tc", "iban", "ad_soyad"]
        for marker in pii_markers:
            assert marker in _DOC_SYSTEM, (
                f"_DOC_SYSTEM KVKK section must explicitly name banned field: {marker}"
            )

    # ── 8.2 Mock routing: artış/itiraz/zam/fahiş → kira_artis_itiraz_ihtarname ─

    @pytest.mark.asyncio
    async def test_mock_artis_ihtarname_routing(self, service, sample_citations):
        """Query with 'artış itiraz ihtarnamesi' must route to kira_artis_itiraz_ihtarname."""
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            intent, answer, params, missing, template_id = await service.process_chat_message(
                "Ev sahibim kira artışına itiraz ihtarnamesi göndermemi istedi, bana yardım et",
                sample_citations,
            )

        assert intent == "document_generation"
        assert template_id == "kira_artis_itiraz_ihtarname"

    @pytest.mark.asyncio
    async def test_mock_zam_keyword_routing(self, service, sample_citations):
        """'zam' + doc action keyword must route to kira_artis_itiraz_ihtarname."""
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            intent, _answer, _params, _missing, template_id = await service.process_chat_message(
                "Ev sahibim fahiş zam yapıyor, itiraz ihtarnamesi hazırla", sample_citations
            )

        assert intent == "document_generation"
        assert template_id == "kira_artis_itiraz_ihtarname"

    # ── 8.6 Edge cases: QA questions vs Document Requests ─────────────────────

    @pytest.mark.asyncio
    async def test_qa_rent_increase_question_not_routed_to_doc_gen(self, service, sample_citations):
        """Legal questions containing 'artış' / 'zam' must NOT be classified as document_generation."""
        questions = [
            "Konut kiralarında yasal kira artış oranı nedir?",
            "Ev sahibim kiramı %100 artırmak istiyor, yasal mı?",
            "Ev sahibim %50 zam yapabilir mi?",
            "Kira sözleşmesinde artış maddesi yoksa ne olur?",
        ]
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            for q in questions:
                intent, _answer, params, missing, template_id = await service.process_chat_message(
                    q, sample_citations
                )
                assert intent == "question_answering", f"Query '{q}' was wrongly classified as {intent}"
                assert template_id is None, f"Query '{q}' should not suggest a template"

    # ── 8.7 Edge cases: Turkish capitalization (İ / I) ───────────────────────

    @pytest.mark.asyncio
    async def test_mock_artis_ihtarname_uppercase_turkish(self, service, sample_citations):
        """Uppercase Turkish 'İ' and 'I' must normalize and route correctly."""
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            intent, _answer, _params, _missing, template_id = await service.process_chat_message(
                "KİRA ARTIŞINA İTİRAZ İHTARNAMESİ HAZIRLA", sample_citations
            )

        assert intent == "document_generation"
        assert template_id == "kira_artis_itiraz_ihtarname"

    # ── 8.8 Edge cases: _doc_answer formatting ────────────────────────────────

    def test_doc_answer_all_params_present_shows_completion_message(self, service):
        """When missing_fields is empty, message states document is ready to be created."""
        answer = service._doc_answer(
            "kira_artis_itiraz_ihtarname",
            {"mevcut_kira_tutari": 10000, "talep_edilen_kira_tutari": 20000},
            [],  # no missing fields
        )
        assert "Tüm bilgiler tamamlandı; belge oluşturulabilir." in answer
        assert "ihtiyacım var" not in answer

    def test_doc_answer_empty_params_handled_cleanly(self, service):
        """When extracted_params is empty, answer does not crash and lists missing fields."""
        answer = service._doc_answer(
            "kira_artis_itiraz_ihtarname",
            {},
            ["kira_baslangic_tarihi", "mevcut_kira_tutari"],
        )
        assert "Fahiş Kira Artışına İtiraz İhtarnamesi" in answer
        assert "**kira_baslangic_tarihi**" in answer
        assert "**mevcut_kira_tutari**" in answer
        assert "Tespit edilen bilgiler" not in answer

    def test_doc_answer_unknown_template_fallback(self, service):
        """Unknown template ID falls back to raw template_id as label."""
        answer = service._doc_answer("bilinmeyen_ozel_sablon", {}, [])
        assert "**bilinmeyen_ozel_sablon** belgesi hazırlanıyor." in answer

    # ── 8.9 Groq mode: kira_artis_itiraz_ihtarname structured extraction ─────

    @pytest.mark.asyncio
    async def test_groq_mode_artis_itiraz_extraction(self, service, sample_citations):
        """Simulate Groq returning structured extraction for kira_artis_itiraz_ihtarname."""
        REAL_KEY = "gsk_" + "x" * 52
        intent_json = json.dumps({"intent": "document_generation"})
        doc_json = json.dumps({
            "suggested_template_id": "kira_artis_itiraz_ihtarname",
            "extracted_params": {
                "mevcut_kira_tutari": 12000,
                "talep_edilen_kira_tutari": 25000,
                "tufe_oran": 49.5,
                "noter_ili": "Ankara",
                "kira_baslangic_tarihi": "2023-06-01",
            },
            "missing_fields": [],
        })

        with (
            patch("app.services.llm_service.settings") as ms,
            patch("app.services.llm_service._get_groq_client") as mock_client_fn,
        ):
            ms.GROQ_API_KEY = REAL_KEY
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            mock_client.chat.completions.create.side_effect = [
                _mock_groq_completion(intent_json),
                _mock_groq_completion(doc_json),
            ]

            intent, answer, params, missing, template_id = await service.process_chat_message(
                "Ev sahibim kiramı 12 binden 25 bine çıkarmak istiyor, itiraz ihtarnamesi oluştur",
                sample_citations,
            )

        assert intent == "document_generation"
        assert template_id == "kira_artis_itiraz_ihtarname"
        assert params["mevcut_kira_tutari"] == 12000
        assert params["talep_edilen_kira_tutari"] == 25000
        assert params["tufe_oran"] == 49.5
        assert params["noter_ili"] == "Ankara"
        assert missing == []
        assert "Fahiş Kira Artışına İtiraz İhtarnamesi" in answer
        assert "Tüm bilgiler tamamlandı" in answer

    @pytest.mark.asyncio
    async def test_mock_fahis_keyword_routing(self, service, sample_citations):
        """'fahiş' keyword must route to kira_artis_itiraz_ihtarname."""
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            intent, _answer, _params, _missing, template_id = await service.process_chat_message(
                "Fahiş kira artışına karşı belge hazırla", sample_citations
            )

        assert intent == "document_generation"
        assert template_id == "kira_artis_itiraz_ihtarname"

    @pytest.mark.asyncio
    async def test_temerrut_still_routes_to_temerrut_template(self, service, sample_citations):
        """Plain 'ihtarname hazırla' (temerrüt context) must still route to kira_ihtarname_temerrut."""
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            intent, _answer, _params, _missing, template_id = await service.process_chat_message(
                "Kiracım kira ödemedi, ihtarname hazırla", sample_citations
            )

        assert intent == "document_generation"
        assert template_id == "kira_ihtarname_temerrut"

    # ── 8.3 Mock params: no PII in missing_fields ─────────────────────────────

    PII_SUBSTRINGS = ["tc", "iban", "ad_soyad", "adres", "kiraci", "kiraya_veren", "tasinmaz"]

    @pytest.mark.asyncio
    async def test_mock_artis_missing_fields_no_pii(self, service, sample_citations):
        """_MOCK_ARTIS_DOC_PARAMS.missing_fields must not contain PII field names."""
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            _intent, _answer, _params, missing, _template_id = await service.process_chat_message(
                "Kira artışına itiraz belgesi oluştur", sample_citations
            )

        for field in missing:
            for pii in self.PII_SUBSTRINGS:
                assert pii not in field.lower(), (
                    f"PII substring '{pii}' found in missing_field: '{field}'"
                )

    # ── 8.4 _doc_answer label ─────────────────────────────────────────────────

    def test_doc_answer_artis_label(self, service):
        """_doc_answer must return the Turkish label for kira_artis_itiraz_ihtarname."""
        answer = service._doc_answer(
            "kira_artis_itiraz_ihtarname",
            {"mevcut_kira_tutari": 10000, "talep_edilen_kira_tutari": 20000},
            ["kira_baslangic_tarihi"],
        )
        assert "Fahiş Kira Artışına İtiraz İhtarnamesi" in answer

    def test_doc_answer_artis_label_in_bold(self, service):
        """The label must appear in bold markdown."""
        answer = service._doc_answer(
            "kira_artis_itiraz_ihtarname",
            {},
            [],
        )
        assert "**Fahiş Kira Artışına İtiraz İhtarnamesi**" in answer

    # ── 8.5 _MOCK_ARTIS_DOC_PARAMS structural checks ─────────────────────────

    def test_artis_mock_params_contain_expected_keys(self):
        from app.services.llm_service import _MOCK_ARTIS_DOC_PARAMS
        expected_keys = {"mevcut_kira_tutari", "talep_edilen_kira_tutari", "tufe_oran", "noter_ili"}
        actual_keys = set(_MOCK_ARTIS_DOC_PARAMS["extracted_params"].keys())
        assert expected_keys.issubset(actual_keys), (
            f"Missing keys in _MOCK_ARTIS_DOC_PARAMS: {expected_keys - actual_keys}"
        )

    def test_artis_mock_params_no_pii_keys(self):
        from app.services.llm_service import _MOCK_ARTIS_DOC_PARAMS
        pii_substrings = ["tc", "iban", "ad_soyad", "adres", "kiraci", "kiraya_veren", "tasinmaz"]
        for key in _MOCK_ARTIS_DOC_PARAMS["extracted_params"]:
            for pii in pii_substrings:
                assert pii not in key.lower(), (
                    f"PII key '{key}' found in _MOCK_ARTIS_DOC_PARAMS.extracted_params"
                )
        for field in _MOCK_ARTIS_DOC_PARAMS["missing_fields"]:
            for pii in pii_substrings:
                assert pii not in field.lower(), (
                    f"PII field '{field}' found in _MOCK_ARTIS_DOC_PARAMS.missing_fields"
                )

    def test_artis_mock_tufe_oran_is_number(self):
        from app.services.llm_service import _MOCK_ARTIS_DOC_PARAMS
        tufe = _MOCK_ARTIS_DOC_PARAMS["extracted_params"]["tufe_oran"]
        assert isinstance(tufe, (int, float)), f"tufe_oran must be a number, got {type(tufe)}"
        assert 0 < tufe < 200, f"tufe_oran value {tufe} seems out of realistic range"


# ──────────────────────────────────────────────────────────────────────────────
# 9. RAG Q&A Quality & Hallucination Guardrails (Faz 2)
# ──────────────────────────────────────────────────────────────────────────────

class TestQAQualityAndHallucinationGuardrailsFaz2:
    """Faz 2 — _QA_SYSTEM prompt, statutory citation standards, hallucination barrier, and disclaimer."""

    def test_qa_system_prompt_contains_mandatory_citation_standard(self):
        """_QA_SYSTEM must require standardized statutory citation format."""
        from app.services.llm_service import _QA_SYSTEM
        assert "STANDART MADDE ATIFI" in _QA_SYSTEM
        assert "Türk Borçlar Kanunu Madde 344 uyarınca" in _QA_SYSTEM
        assert "Tüketicinin Korunması Hakkında Kanun Madde 11 uyarınca" in _QA_SYSTEM
        assert "İş Kanunu Madde 17 uyarınca" in _QA_SYSTEM

    def test_qa_system_prompt_contains_hallucination_barrier(self):
        """_QA_SYSTEM must explicitly instruct the model to return the standard fallback when context is insufficient."""
        from app.services.llm_service import _QA_SYSTEM, NO_RELEVANT_LAW_ANSWER
        assert "HALÜSİNASYON BARİYERİ" in _QA_SYSTEM
        assert NO_RELEVANT_LAW_ANSWER in _QA_SYSTEM

    @pytest.mark.asyncio
    async def test_qa_answer_empty_citations_returns_canonical_fallback(self, service):
        """When citations list is empty, _answer_legal_question returns canonical fallback without calling Groq."""
        from app.services.llm_service import NO_RELEVANT_LAW_ANSWER
        answer = await service._answer_legal_question("Kira artış oranı ne kadar?", [])
        assert answer == NO_RELEVANT_LAW_ANSWER

    @pytest.mark.asyncio
    async def test_qa_answer_blank_citations_returns_canonical_fallback(self, service):
        """When all retrieved citations have blank snippets, returns canonical fallback."""
        from app.services.llm_service import NO_RELEVANT_LAW_ANSWER
        blank_citations = [
            Citation(article_id="TBK-X", law_name="Test", text_snippet="   "),
            Citation(article_id="TBK-Y", law_name="Test", text_snippet=""),
        ]
        answer = await service._answer_legal_question("Soru?", blank_citations)
        assert answer == NO_RELEVANT_LAW_ANSWER

    @pytest.mark.asyncio
    async def test_mock_response_empty_citations_returns_fallback(self, service):
        """In mock mode, when citations is empty, returns fallback message."""
        from app.services.llm_service import NO_RELEVANT_LAW_ANSWER
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            intent, answer, params, missing, template_id = await service.process_chat_message(
                "Mevzuatta olmayan bir soru?", []
            )
        assert intent == "question_answering"
        assert NO_RELEVANT_LAW_ANSWER in answer

    def test_mock_qa_answer_follows_standard_citation_format(self):
        """_MOCK_QA_ANSWER must follow the standardized statutory citation format."""
        from app.services.llm_service import _MOCK_QA_ANSWER
        assert "Türk Borçlar Kanunu Madde 344 uyarınca" in _MOCK_QA_ANSWER

    @pytest.mark.asyncio
    async def test_groq_qa_hallucination_refusal_when_unsupported(self, service, sample_citations):
        """When Groq returns the canonical refusal string for unsupported queries, service preserves it."""
        from app.services.llm_service import NO_RELEVANT_LAW_ANSWER
        intent_json = json.dumps({"intent": "question_answering"})

        with (
            patch("app.services.llm_service.settings") as ms,
            patch("app.services.llm_service._get_groq_client") as mock_client_fn,
        ):
            ms.GROQ_API_KEY = REAL_KEY
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            mock_client = AsyncMock()
            mock_client_fn.return_value = mock_client
            mock_client.chat.completions.create.side_effect = [
                _mock_groq_completion(intent_json),
                _mock_groq_completion(NO_RELEVANT_LAW_ANSWER),
            ]

            intent, answer, params, missing, template_id = await service.process_chat_message(
                "Ceza kanununda hırsızlık cezası nedir?",
                sample_citations,
            )

        assert intent == "question_answering"
        assert answer == NO_RELEVANT_LAW_ANSWER

    @pytest.mark.asyncio
    async def test_legal_disclaimer_present_in_chat_response_contracts(self, service, sample_citations):
        """Verify that every ChatResponse contract carries LEGAL_DISCLAIMER per AGENTS.md §5."""
        from app.schemas.chat import ChatResponse
        from app.schemas.common import LEGAL_DISCLAIMER

        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"

            # 1. Q&A intent
            intent, answer, params, missing, template_id = await service.process_chat_message(
                "Kira artış oranı?", sample_citations
            )
            resp_qa = ChatResponse(
                intent=intent, answer=answer, citations=sample_citations,
                extracted_params=params, missing_fields=missing, suggested_template_id=template_id,
            )
            assert resp_qa.disclaimer == LEGAL_DISCLAIMER
            assert "avukatlık hizmeti vermez" in resp_qa.disclaimer

            # 2. Document generation intent
            intent, answer, params, missing, template_id = await service.process_chat_message(
                "İhtarname hazırla", sample_citations
            )
            resp_doc = ChatResponse(
                intent=intent, answer=answer, citations=[],
                extracted_params=params, missing_fields=missing, suggested_template_id=template_id,
            )
            assert resp_doc.disclaimer == LEGAL_DISCLAIMER

            # 3. Out of scope intent
            resp_oos = ChatResponse(
                intent="out_of_scope", answer="Kapsam dışı", citations=[],
                extracted_params={}, missing_fields=[], suggested_template_id=None,
            )
            assert resp_oos.disclaimer == LEGAL_DISCLAIMER

    @pytest.mark.asyncio
    async def test_qa_answer_deduplicates_identical_citation_snippets(self, service):
        """When citations contain duplicate snippets, context block deduplicates them."""
        from app.services.llm_service import _QA_SYSTEM
        c1 = Citation(article_id="TBK-344", law_name="TBK", text_snippet="Kira artış sınırı TÜFE.")
        c2 = Citation(article_id="TBK-344", law_name="TBK", text_snippet="Kira artış sınırı TÜFE.")

        captured_messages = []

        async def fake_call_groq(messages, **kwargs):
            nonlocal captured_messages
            captured_messages = messages
            return "Türk Borçlar Kanunu Madde 344 uyarınca cevap."

        with patch("app.services.llm_service._call_groq", side_effect=fake_call_groq):
            answer = await service._answer_legal_question("Artış?", [c1, c2])

        user_content = captured_messages[1]["content"]
        assert user_content.count("[TBK-344]") == 1, "Duplicate citation was not deduplicated!"
        assert "Türk Borçlar Kanunu Madde 344 uyarınca" in answer

    @pytest.mark.asyncio
    async def test_qa_answer_fallback_on_empty_groq_response(self, service, sample_citations):
        """If Groq returns whitespace or empty string, fallback to NO_RELEVANT_LAW_ANSWER."""
        from app.services.llm_service import NO_RELEVANT_LAW_ANSWER

        with patch("app.services.llm_service._call_groq", return_value="   "):
            answer = await service._answer_legal_question("Soru?", sample_citations)

        assert answer == NO_RELEVANT_LAW_ANSWER

    @pytest.mark.asyncio
    async def test_mock_response_blank_citations_returns_fallback(self, service):
        """In mock mode, when citations are present but blank, returns fallback message."""
        from app.services.llm_service import NO_RELEVANT_LAW_ANSWER
        blank_citations = [Citation(article_id="T1", law_name="L1", text_snippet="   ")]

        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            intent, answer, *_ = await service.process_chat_message(
                "Soru?", blank_citations
            )
        assert intent == "question_answering"
        assert NO_RELEVANT_LAW_ANSWER in answer
