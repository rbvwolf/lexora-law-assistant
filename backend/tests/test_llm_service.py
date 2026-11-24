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

    def test_different_temperature_different_hash(self):
        msgs = [{"role": "user", "content": "A"}]
        assert _cache_key("m", msgs, temperature=0.0) != _cache_key("m", msgs, temperature=0.2)

    def test_different_response_format_different_hash(self):
        msgs = [{"role": "user", "content": "A"}]
        assert _cache_key("m", msgs, response_format={"type": "json_object"}) != _cache_key("m", msgs, response_format=None)


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
            intent, answer, params, missing, template_id = await service.process_chat_message(
                "Ayıplı ürün dilekçesi yaz", sample_citations
            )

        assert intent == "document_generation"
        assert template_id == "tuketici_ayipli_mal_ihtarname"
        assert "MOCK" in answer
        assert "Ayıplı Mal Tüketici Başvurusu" in answer
        assert isinstance(params, dict)
        assert isinstance(missing, list)


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
        qa_answer = "TBK Madde 315 uyarınca kiracı temerrüde düşerse sözleşme feshedilebilir."

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
        # Mock mode must never return PII keys or PII-like substrings in missing_fields
        pii_substrings = ("tc", "iban", "ad_soyad", "adres", "telefon", "banka_hesap", "kiraci", "kiraya_veren", "tasinmaz")
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
            _, _, _, missing_fields, _ = await service.process_chat_message(
                "İhtarname oluştur", sample_citations
            )

        assert missing_fields == ["odeme_suresi_gun"]
        for field in missing_fields:
            lowered = field.lower()
            assert lowered not in self.PII_FIELD_NAMES, (
                f"PII field '{field}' leaked into missing_fields!"
            )
            assert not any(sub in lowered for sub in pii_substrings), (
                f"PII substring leaked into missing_fields: '{field}'"
            )

    @pytest.mark.asyncio
    async def test_groq_mode_pii_not_in_missing_fields(self, service, sample_citations):
        """Even when Groq returns PII in missing_fields or extracted_params, server strips them."""
        intent_json = json.dumps({"intent": "document_generation"})
        # Simulate a badly-behaved LLM response that includes PII field names
        bad_doc_json = json.dumps({
            "suggested_template_id": "kira_ihtarname_temerrut",
            "extracted_params": {
                "uyusmazlik_turu": "Kira",
                "iban": "TR120000000000000000000000",
                "kiraci_adres": "İstanbul",
            },
            "missing_fields": ["kira_tutari", "tc_kimlik", "banka_hesap_bilgisi"],
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

            _, _, extracted_params, missing_fields, _ = await service.process_chat_message(
                "İhtarname hazırla, TC kimliğim 12345678901",
                sample_citations,
            )

        assert "tc_kimlik" not in missing_fields
        assert "banka_hesap_bilgisi" not in missing_fields
        assert missing_fields == ["kira_tutari"]
        assert "iban" not in extracted_params
        assert "kiraci_adres" not in extracted_params
        assert extracted_params == {"uyusmazlik_turu": "Kira"}


# ──────────────────────────────────────────────────────────────────────────────
# 7. Edge cases
# ──────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:

    @pytest.mark.asyncio
    async def test_empty_citations_qa_returns_guidance(self, service):
        """When RAG returns nothing, Q&A returns NO_RELEVANT_LAW_ANSWER without calling Groq for Q&A."""
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
            mock_client.chat.completions.create.return_value = _mock_groq_completion(intent_json)

            intent, answer, *_ = await service.process_chat_message(
                "Bir sorum var", []  # empty citations
            )

        assert intent == "question_answering"
        assert answer == NO_RELEVANT_LAW_ANSWER
        assert mock_client.chat.completions.create.await_count == 1

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
        with patch("app.services.llm_service._call_groq", new_callable=AsyncMock) as mock_call:
            answer = await service._answer_legal_question("Kira artış oranı ne kadar?", [])
        assert answer == NO_RELEVANT_LAW_ANSWER
        mock_call.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_qa_answer_blank_citations_returns_canonical_fallback(self, service):
        """When all retrieved citations have blank snippets, returns canonical fallback without calling Groq."""
        from app.services.llm_service import NO_RELEVANT_LAW_ANSWER
        blank_citations = [
            Citation(article_id="TBK-X", law_name="Test", text_snippet="   "),
            Citation(article_id="TBK-Y", law_name="Test", text_snippet=""),
        ]
        with patch("app.services.llm_service._call_groq", new_callable=AsyncMock) as mock_call:
            answer = await service._answer_legal_question("Soru?", blank_citations)
        assert answer == NO_RELEVANT_LAW_ANSWER
        mock_call.assert_not_awaited()

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
            assert "avukatlık hizmeti vermez" in resp_doc.disclaimer

            # 3. Out of scope intent
            intent, answer, params, missing, template_id = await service.process_chat_message(
                "Bugün hava nasıl?", sample_citations
            )
            assert intent == "out_of_scope"
            resp_oos = ChatResponse(
                intent=intent, answer=answer, citations=[],
                extracted_params=params, missing_fields=missing, suggested_template_id=template_id,
            )
            assert resp_oos.disclaimer == LEGAL_DISCLAIMER
            assert "avukatlık hizmeti vermez" in resp_oos.disclaimer

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

    @pytest.mark.asyncio
    async def test_call_groq_model_name_override(self):
        """When model_name is provided, _call_groq passes it to Groq completions and cache."""
        from app.services.llm_service import _call_groq, _response_cache, _cache_key

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Judge evaluation response"
        mock_completion.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        messages = [{"role": "user", "content": "test prompt"}]

        with patch("app.services.llm_service._get_groq_client", return_value=mock_client):
            res = await _call_groq(messages, model_name="custom-judge-model-8b")

        assert res == "Judge evaluation response"
        mock_client.chat.completions.create.assert_awaited_once()
        _, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["model"] == "custom-judge-model-8b"

        # _call_groq must not populate _response_cache directly; callers cache after validation
        expected_key = _cache_key("custom-judge-model-8b", messages)
        assert expected_key not in _response_cache

    @pytest.mark.asyncio
    async def test_call_groq_default_model_name_uses_settings(self):
        """When model_name=None, _call_groq falls back to settings.GROQ_MODEL_NAME."""
        from app.services.llm_service import _call_groq

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Standard response"
        mock_completion.choices = [mock_choice]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        messages = [{"role": "user", "content": "default test"}]

        with (
            patch("app.services.llm_service.settings.GROQ_MODEL_NAME", "llama-default-model"),
            patch("app.services.llm_service._get_groq_client", return_value=mock_client),
        ):
            res = await _call_groq(messages, model_name=None)

        assert res == "Standard response"
        _, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["model"] == "llama-default-model"



# ──────────────────────────────────────────────────────────────────────────────
# 10. Batch 1 Hardening: Citations, Non-dict JSON, Bounded Cache, Thesaurus İ
# ──────────────────────────────────────────────────────────────────────────────

class TestBatch1Hardening:
    """Tests for citation grounding, JSON type guards, bounded cache, mock routing, and Turkish İ thesaurus."""

    @pytest.mark.asyncio
    async def test_qa_rejects_unretrieved_article_citation(self, service, sample_citations):
        """Answer citing an article not in retrieved citations falls back to NO_RELEVANT_LAW_ANSWER and is not cached."""
        from app.services.llm_service import NO_RELEVANT_LAW_ANSWER

        hallucinated = "Türk Borçlar Kanunu Madde 999 uyarınca kiracı derhal tahliye edilir."
        with patch("app.services.llm_service._call_groq", return_value=hallucinated):
            answer = await service._answer_legal_question("Kiracı tahliye?", sample_citations)

        assert answer == NO_RELEVANT_LAW_ANSWER
        assert len(_response_cache) == 0

    @pytest.mark.asyncio
    async def test_qa_rejects_wrong_law_for_retrieved_article(self, service, sample_citations):
        """Answer citing TCK Madde 315 when only TBK-315 was retrieved falls back to NO_RELEVANT_LAW_ANSWER."""
        from app.services.llm_service import NO_RELEVANT_LAW_ANSWER

        wrong_law = "TCK Madde 315 uyarınca işlem yapılır."
        with patch("app.services.llm_service._call_groq", return_value=wrong_law):
            answer = await service._answer_legal_question("Kiracı temerrüt?", sample_citations)

        assert answer == NO_RELEVANT_LAW_ANSWER

    @pytest.mark.asyncio
    async def test_qa_rejects_answer_without_any_citation(self, service, sample_citations):
        """Answer omitting statutory citations falls back to NO_RELEVANT_LAW_ANSWER."""
        from app.services.llm_service import NO_RELEVANT_LAW_ANSWER

        uncited = "Kiracı kirayı ödemezse ev sahibi sözleşmeyi feshedebilir."
        with patch("app.services.llm_service._call_groq", return_value=uncited):
            answer = await service._answer_legal_question("Kiracı ödemezse?", sample_citations)

        assert answer == NO_RELEVANT_LAW_ANSWER

    @pytest.mark.asyncio
    async def test_classify_intent_non_dict_json_falls_back(self, service):
        """Non-dict JSON (e.g. list or string) in _classify_intent falls back to out_of_scope without caching."""
        for payload in ('["question_answering"]', '"document_generation"', "123"):
            _response_cache.clear()
            with patch("app.services.llm_service._call_groq", return_value=payload):
                intent = await service._classify_intent("Kira sorusu")
            assert intent == "out_of_scope"
            assert len(_response_cache) == 0

    @pytest.mark.asyncio
    async def test_extract_doc_params_non_dict_json_and_invalid_template(self, service):
        """Non-dict JSON returns safe defaults; unknown template_id falls back to kira_ihtarname_temerrut."""
        with patch("app.services.llm_service._call_groq", return_value='["not", "a", "dict"]'):
            tpl, params, missing = await service._extract_doc_params("İhtarname hazırla")
        assert tpl == "kira_ihtarname_temerrut"
        assert params == {}
        assert missing == ["uyusmazlik_turu", "kira_tutari"]
        assert len(_response_cache) == 0

        bad_tpl_json = json.dumps({
            "suggested_template_id": "uydurma_sablon",
            "extracted_params": "not_a_dict",
            "missing_fields": "not_a_list",
        })
        with patch("app.services.llm_service._call_groq", return_value=bad_tpl_json):
            tpl2, params2, missing2 = await service._extract_doc_params("İhtarname hazırla")
        assert tpl2 == "kira_ihtarname_temerrut"
        assert params2 == {}
        assert missing2 == []

    @pytest.mark.asyncio
    async def test_call_groq_empty_choices_returns_empty_string(self):
        """_call_groq handles empty completion.choices without raising IndexError."""
        from app.services.llm_service import _call_groq

        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices = []
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        with patch("app.services.llm_service._get_groq_client", return_value=mock_client):
            res = await _call_groq([{"role": "user", "content": "test"}])

        assert res == ""

    def test_response_cache_bounded_lru_eviction(self):
        """_cache_set evicts oldest entries once _RESPONSE_CACHE_MAX_SIZE is exceeded."""
        from app.services.llm_service import _RESPONSE_CACHE_MAX_SIZE, _cache_set

        for i in range(_RESPONSE_CACHE_MAX_SIZE + 5):
            _cache_set(f"k-{i}", f"v-{i}")

        assert len(_response_cache) == _RESPONSE_CACHE_MAX_SIZE
        assert "k-0" not in _response_cache
        assert f"k-{_RESPONSE_CACHE_MAX_SIZE + 4}" in _response_cache

    @pytest.mark.asyncio
    async def test_mock_qa_vs_doc_and_out_of_scope(self, service, sample_citations):
        """Q&A queries with 'fesih', 'yazılı', or 'belgeler' stay question_answering; off-topic is out_of_scope."""
        with patch("app.services.llm_service.settings") as ms:
            ms.GROQ_API_KEY = "gsk_mock_key_for_dev_mode"
            ms.GROQ_MODEL_NAME = "llama-3.3-70b-versatile"

            for qa_msg in (
                "Sözleşme fesih şartları nedir?",
                "Yazılı kira sözleşmesi şart mı?",
                "Fesih için hangi belgeler gerekir?",
            ):
                intent, *_ = await service.process_chat_message(qa_msg, sample_citations)
                assert intent == "question_answering", f"Expected Q&A for: {qa_msg}"

            intent_oos, *_ = await service.process_chat_message("Bugün hava nasıl?", sample_citations)
            assert intent_oos == "out_of_scope"

    def test_thesaurus_turkish_uppercase_i_and_rental_context(self):
        """Thesaurus normalizes Turkish İ/I before regex matching and requires rental context for % raise."""
        from app.core.thesaurus import legal_thesaurus

        expanded_kira = legal_thesaurus.expand_query("KİRA ARTIŞI NE KADAR?")
        assert "tüfe" in expanded_kira

        expanded_is = legal_thesaurus.expand_query("İŞTEN ÇIKARILDIM")
        assert "iş sözleşmesinin feshi" in expanded_is

        salary_query = legal_thesaurus.expand_query("Maaşıma %30 zam yapıldı")
        assert "kira bedelinin belirlenmesi" not in salary_query
        assert "ücret" in salary_query
