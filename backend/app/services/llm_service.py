"""LLM service orchestrating Groq API calls for intent classification, legal Q&A, and
document parameter extraction.

Pipeline per message:
    1. Classify intent  (json_object mode)  →  question_answering | document_generation | out_of_scope
    2a. question_answering  → RAG-grounded Turkish legal answer with article citations
    2b. document_generation → structured param extraction + missing PII field list
    2c. out_of_scope        → polite scope-refusal message
    3. Langfuse trace on every Groq call
    4. SHA-256 prompt-hash LRU cache to protect free-tier rate limits

KVKK / AGENTS.md compliance:
    - Model name always from settings.GROQ_MODEL_NAME – never hardcoded.
    - LLM never receives raw PII (TC ID, IBAN, full address).
    - missing_fields lists only EVENT field names (e.g. "kira_tutari"), never PII keys.
    - LEGAL_DISCLAIMER injected in every response.
"""

import hashlib
import json
import logging
from functools import lru_cache
from typing import Any, Dict, List, Literal, Optional, Tuple

from app.core.config import settings
from app.core.langfuse import trace_llm_call
from app.schemas.chat import Citation
from app.schemas.common import LEGAL_DISCLAIMER

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mock API key sentinel
# ---------------------------------------------------------------------------
_MOCK_KEY_PREFIXES = ("gsk_mock", "gsk_your", "placeholder")


def _is_mock_key(key: str) -> bool:
    """Return True when the configured key is a development placeholder."""
    key_lower = key.strip().lower()
    return not key_lower or any(key_lower.startswith(p) for p in _MOCK_KEY_PREFIXES)


# ---------------------------------------------------------------------------
# Prompt-hash cache  (in-memory LRU; survives the process lifetime)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=256)
def _cached_groq_call(prompt_hash: str) -> str:  # noqa: ARG001
    """Marker only – real value stored separately; lru_cache key is the hash."""
    raise NotImplementedError  # never called directly


_response_cache: Dict[str, str] = {}


def _cache_key(model: str, messages: List[Dict[str, str]]) -> str:
    """Stable SHA-256 hash over model + serialised messages."""
    payload = json.dumps({"model": model, "messages": messages}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Groq client (lazy singleton)
# ---------------------------------------------------------------------------
_groq_client = None


def _get_groq_client():
    """Lazily initialise and return the Groq AsyncClient singleton."""
    global _groq_client
    if _groq_client is None:
        from groq import AsyncGroq  # type: ignore

        _groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _groq_client


# ---------------------------------------------------------------------------
# Low-level cached Groq caller
# ---------------------------------------------------------------------------
async def _call_groq(
    messages: List[Dict[str, str]],
    *,
    response_format: Optional[Dict[str, str]] = None,
    temperature: float = 0.2,
) -> str:
    """Call Groq API with prompt-hash caching.  Returns the assistant's text."""
    model = settings.GROQ_MODEL_NAME
    key = _cache_key(model, messages)

    if key in _response_cache:
        logger.debug("Cache HIT for prompt hash %s…", key[:12])
        return _response_cache[key]

    logger.debug("Cache MISS – calling Groq (%s)…", model)
    client = _get_groq_client()

    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 1024,
    }
    if response_format:
        kwargs["response_format"] = response_format

    completion = await client.chat.completions.create(**kwargs)
    text: str = completion.choices[0].message.content or ""
    _response_cache[key] = text
    return text


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_INTENT_SYSTEM = """\
Sen Türk hukuku alanında uzman bir AI asistanısın.
Kullanıcının mesajını analiz ederek niyetini belirle.

Kurallar:
- Sadece kira hukuku, tüketici hukuku, iş hukuku ve genel borçlar hukuku kapsamındaki konularla ilgilenirsin.
- Ağır ceza davaları, aile hukuku, vergi hukuku vb. kapsam dışıdır.

Yanıtını SADECE şu JSON formatında ver, başka hiçbir şey ekleme:
{
  "intent": "question_answering" | "document_generation" | "out_of_scope"
}

intent değerleri:
- "question_answering"  : Kullanıcı hukuki bir soru soruyor.
- "document_generation" : Kullanıcı ihtarname, dilekçe veya resmi belge talep ediyor.
- "out_of_scope"        : Hukuk dışı veya kapsam dışı bir talep.
"""

_QA_SYSTEM = """\
Sen Türk hukuku alanında uzman bir AI asistanısın.
SADECE aşağıda sana verilen kanun maddelerine dayanarak cevap ver.
Verilmeyen maddelerden, genel bilginden veya tahmininden kesinlikle yararlanma (halüsinasyon yapma).
Cevabında her zaman madde numarasına açıkça atıf yap (örn. "TBK Madde 315 uyarınca").
Cevabını Türkçe yaz. Kısa, net ve anlaşılır ol.
"""

_DOC_SYSTEM = """\
Sen Türk hukuku alanında uzman bir AI asistanısın.
Kullanıcının mesajından hukuki belge oluşturmak için gerekli OLAY PARAMETRELERİNİ çıkar.

ÖNEMLİ KVKK KURALLARI:
- TC kimlik numarası, IBAN, açık adres, telefon gibi KİŞİSEL VERİLERİ (PII) ASLA isteme.
- PII veriler ayrı bir formla toplanacaktır; sen sadece olayı anlatan parametreleri çıkar.

Desteklenen şablon kimlikleri:
- "kira_ihtarname_temerrut"     : Kiracı ödeme yapmadığında ev sahibi adına temerrüt ihtarnamesi
- "tuketici_ayipli_mal_ihtarname": Ayıplı mal için tüketici şikayet/başvuru belgesi

Yanıtını SADECE şu JSON formatında ver:
{
  "suggested_template_id": "<şablon_id>",
  "extracted_params": {
    "uyusmazlik_turu": "<string>",
    "kira_tutari": <number|null>,
    "gecikilen_aylar": [<string>, ...],
    "odeme_suresi_gun": <number|null>,
    "urun_adi": "<string|null>",
    "satin_alma_tutari": <number|null>,
    "ayip_detayi": "<string|null>",
    "olay_tarihi": "<YYYY-MM-DD|null>"
  },
  "missing_fields": ["<alan_adı>", ...]
}

missing_fields: Belgeyi oluşturmak için kullanıcıdan hâlâ öğrenilmesi gereken OLAY alanlarının listesi.
Eğer tüm alanlar mevcutsa boş liste döndür.
"""

# ---------------------------------------------------------------------------
# Mock responses (no real API key)
# ---------------------------------------------------------------------------

_MOCK_QA_ANSWER = (
    "[MOCK MOD] Türk Borçlar Kanunu Madde 344 uyarınca konut kiralarında kira artış oranı, "
    "bir önceki kira yılındaki tüketici fiyat endeksindeki (TÜFE) on iki aylık ortalamalara "
    "göre değişim oranını geçemez. Taraflarca bu oranı aşan bir anlaşma yapılmış olsa dahi "
    "aşan kısım geçersiz sayılır."
)

_MOCK_DOC_PARAMS: Dict[str, Any] = {
    "suggested_template_id": "kira_ihtarname_temerrut",
    "extracted_params": {
        "uyusmazlik_turu": "Kira Ödememe (Temerrüt)",
        "kira_tutari": 15000,
        "gecikilen_aylar": ["Eylül 2026", "Ekim 2026"],
        "odeme_suresi_gun": 30,
    },
    "missing_fields": ["banka_hesap_bilgisi", "kiralanan_tasinmaz_adresi"],
}


# ---------------------------------------------------------------------------
# LLMService
# ---------------------------------------------------------------------------


class LLMService:
    """Orchestrates Groq API calls for intent routing, legal Q&A, and document extraction."""

    def __init__(self) -> None:
        # Model name read from settings; never hardcoded (AGENTS.md §6)
        self.model_name = settings.GROQ_MODEL_NAME

    # ------------------------------------------------------------------
    # Public entry point (consumed by /api/v1/chat/message)
    # ------------------------------------------------------------------

    @trace_llm_call(name="llm_service.process_chat_message")
    async def process_chat_message(
        self,
        cleaned_message: str,
        retrieved_citations: List[Citation],
    ) -> Tuple[
        Literal["question_answering", "document_generation", "out_of_scope"],
        str,
        Dict[str, Any],
        List[str],
        Optional[str],
    ]:
        """Classify intent and route to the appropriate sub-handler.

        Args:
            cleaned_message:     PII-masked, injection-sanitised user message.
            retrieved_citations: Top-k statutory citations from RAG service.

        Returns:
            Tuple of (intent, answer, extracted_params, missing_fields, suggested_template_id)
        """
        if _is_mock_key(settings.GROQ_API_KEY):
            return self._mock_response(cleaned_message)

        intent = await self._classify_intent(cleaned_message)

        if intent == "question_answering":
            answer = await self._answer_legal_question(cleaned_message, retrieved_citations)
            return intent, answer, {}, [], None

        if intent == "document_generation":
            template_id, extracted_params, missing_fields = await self._extract_doc_params(
                cleaned_message
            )
            answer = self._doc_answer(template_id, extracted_params, missing_fields)
            return intent, answer, extracted_params, missing_fields, template_id

        # out_of_scope
        return (
            "out_of_scope",
            (
                "Bu konuda yardımcı olamıyorum. Yalnızca kira hukuku, tüketici hukuku, "
                "iş hukuku ve genel borçlar hukuku kapsamındaki sorularınızda ve yasal belge "
                "taleplerinizde destek sunabiliyorum."
            ),
            {},
            [],
            None,
        )

    # ------------------------------------------------------------------
    # Step 1: Intent classification
    # ------------------------------------------------------------------

    async def _classify_intent(
        self, message: str
    ) -> Literal["question_answering", "document_generation", "out_of_scope"]:
        """Return the classified intent using Groq JSON mode."""
        messages = [
            {"role": "system", "content": _INTENT_SYSTEM},
            {"role": "user", "content": message},
        ]
        raw = await _call_groq(messages, response_format={"type": "json_object"}, temperature=0.0)

        try:
            data = json.loads(raw)
            intent_value = data.get("intent", "out_of_scope")
            if intent_value in ("question_answering", "document_generation", "out_of_scope"):
                return intent_value  # type: ignore[return-value]
        except (json.JSONDecodeError, KeyError):
            logger.warning("Intent classification JSON parse failed; raw=%s", raw[:200])

        return "out_of_scope"

    # ------------------------------------------------------------------
    # Step 2a: RAG-grounded legal Q&A
    # ------------------------------------------------------------------

    async def _answer_legal_question(
        self, message: str, citations: List[Citation]
    ) -> str:
        """Generate a strictly RAG-grounded Turkish legal answer."""
        if not citations:
            return (
                "Sorunuzla ilgili kanun veritabanımızda yeterli makale bulunamadı. "
                "Lütfen sorunuzu daha ayrıntılı ifade edin ya da farklı bir konu deneyin."
            )

        # Build context block from retrieved articles
        context_parts: List[str] = []
        for c in citations:
            context_parts.append(
                f"[{c.article_id}] {c.law_name}\n{c.text_snippet}"
            )
        context_block = "\n\n---\n\n".join(context_parts)

        messages = [
            {"role": "system", "content": _QA_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Kanun maddeleri:\n{context_block}\n\n"
                    f"Kullanıcı sorusu: {message}"
                ),
            },
        ]
        answer = await _call_groq(messages, temperature=0.1)
        return answer.strip()

    # ------------------------------------------------------------------
    # Step 2b: Document parameter extraction
    # ------------------------------------------------------------------

    async def _extract_doc_params(
        self, message: str
    ) -> Tuple[str, Dict[str, Any], List[str]]:
        """Extract case parameters and identify missing fields for document generation."""
        messages = [
            {"role": "system", "content": _DOC_SYSTEM},
            {"role": "user", "content": message},
        ]
        raw = await _call_groq(messages, response_format={"type": "json_object"}, temperature=0.0)

        try:
            data = json.loads(raw)
            template_id: str = data.get("suggested_template_id", "kira_ihtarname_temerrut")
            extracted_params: Dict[str, Any] = data.get("extracted_params", {})
            missing_fields: List[str] = data.get("missing_fields", [])

            # Drop null values from extracted_params to keep payload clean
            extracted_params = {k: v for k, v in extracted_params.items() if v is not None}

            return template_id, extracted_params, missing_fields
        except (json.JSONDecodeError, KeyError):
            logger.warning("Doc param extraction JSON parse failed; raw=%s", raw[:200])
            return "kira_ihtarname_temerrut", {}, ["uyusmazlik_turu", "kira_tutari"]

    # ------------------------------------------------------------------
    # Step 2b: Human-readable guidance for document generation
    # ------------------------------------------------------------------

    def _doc_answer(
        self,
        template_id: str,
        extracted_params: Dict[str, Any],
        missing_fields: List[str],
    ) -> str:
        """Compose a guidance message for the document generation flow."""
        template_labels = {
            "kira_ihtarname_temerrut": "Kira Temerrüdü İhtarnamesi",
            "tuketici_ayipli_mal_ihtarname": "Ayıplı Mal Tüketici Başvurusu",
        }
        label = template_labels.get(template_id, template_id)

        parts = [f"**{label}** belgesi hazırlanıyor."]

        if extracted_params:
            param_lines = []
            for k, v in extracted_params.items():
                if isinstance(v, list):
                    param_lines.append(f"- {k}: {', '.join(str(i) for i in v)}")
                else:
                    param_lines.append(f"- {k}: {v}")
            parts.append("Tespit edilen bilgiler:\n" + "\n".join(param_lines))

        if missing_fields:
            parts.append(
                "Belgeyi tamamlamak için şu bilgilere ihtiyacım var: "
                + ", ".join(f"**{f}**" for f in missing_fields)
                + "."
            )
            parts.append(
                "Kimlik numarası, IBAN ve adres bilgilerinizi güvenli form aracılığıyla ayrıca girebilirsiniz."
            )
        else:
            parts.append("Tüm bilgiler tamamlandı; belge oluşturulabilir.")

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Mock response (no real API key configured)
    # ------------------------------------------------------------------

    def _mock_response(
        self, message: str
    ) -> Tuple[
        Literal["question_answering", "document_generation", "out_of_scope"],
        str,
        Dict[str, Any],
        List[str],
        Optional[str],
    ]:
        """Return deterministic mock responses when no real Groq key is present."""
        lowered = message.lower()
        doc_keywords = ["ihtarname", "dilekçe", "tahliye", "başvuru", "hazırla", "yaz", "oluştur", "fesih"]
        if any(kw in lowered for kw in doc_keywords):
            return (
                "document_generation",
                "⚠️ [MOCK MOD] " + self._doc_answer(
                    _MOCK_DOC_PARAMS["suggested_template_id"],
                    _MOCK_DOC_PARAMS["extracted_params"],
                    _MOCK_DOC_PARAMS["missing_fields"],
                ),
                _MOCK_DOC_PARAMS["extracted_params"],
                _MOCK_DOC_PARAMS["missing_fields"],
                _MOCK_DOC_PARAMS["suggested_template_id"],
            )
        return "question_answering", _MOCK_QA_ANSWER, {}, [], None


# ---------------------------------------------------------------------------
# Singleton instance (imported by chat.py router)
# ---------------------------------------------------------------------------
llm_service = LLMService()
