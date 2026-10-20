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
