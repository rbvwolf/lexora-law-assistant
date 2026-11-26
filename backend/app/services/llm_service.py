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

import asyncio
from collections import OrderedDict
import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

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
# Prompt-hash cache  (bounded in-memory LRU; survives the process lifetime)
# ---------------------------------------------------------------------------
_RESPONSE_CACHE_MAX_SIZE = 256
_response_cache: OrderedDict[str, str] = OrderedDict()


def _cache_set(key: str, value: str) -> None:
    """Store a validated response in the bounded LRU cache."""
    _response_cache[key] = value
    _response_cache.move_to_end(key)
    while len(_response_cache) > _RESPONSE_CACHE_MAX_SIZE:
        _response_cache.popitem(last=False)


def _cache_key(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    response_format: Optional[Dict[str, str]] = None,
) -> str:
    """Stable SHA-256 hash over model + serialised messages + temperature + response_format."""
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "response_format": response_format,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Groq client (lazy singleton)
# ---------------------------------------------------------------------------
_groq_client = None


class LLMRateLimitedError(Exception):
    """Groq answered 429 and the wait it asked for does not fit the per-request budget."""

    def __init__(self, retry_after_seconds: Optional[float] = None) -> None:
        super().__init__("Groq rate limit exceeded")
        self.retry_after_seconds = retry_after_seconds


class LLMUnavailableError(Exception):
    """Groq could not be reached, timed out, or kept answering 5xx."""


def _get_groq_client():
    """Lazily initialise and return the Groq AsyncClient singleton.

    The SDK's own retries are off (max_retries=0): it would sleep for the full Retry-After
    (~25 s on the free tier) inside the user's request. _call_groq retries under a budget instead.
    """
    global _groq_client
    if _groq_client is None:
        from groq import AsyncGroq  # type: ignore

        _groq_client = AsyncGroq(
            api_key=settings.GROQ_API_KEY,
            max_retries=0,
            timeout=settings.GROQ_TIMEOUT_SECONDS,
        )
    return _groq_client


def _retry_after_seconds(exc: Exception) -> Optional[float]:
    """Seconds from the 429's retry-after-ms / retry-after headers, if present and numeric."""
    headers = getattr(getattr(exc, "response", None), "headers", None)
    if not headers:
        return None
    for name, scale in (("retry-after-ms", 0.001), ("retry-after", 1.0)):
        raw = headers.get(name)
        if raw is None:
            continue
        try:
            value = float(raw) * scale
        except (TypeError, ValueError):
            continue
        if value >= 0 and value == value:  # not NaN
            return value
    return None


# Pause before retrying a transient 5xx / connection error (not a 429)
_TRANSIENT_RETRY_DELAY_SECONDS = 0.5

# Indirection so tests can record waits without sleeping
_sleep = asyncio.sleep


# ---------------------------------------------------------------------------
# Low-level cached Groq caller
# ---------------------------------------------------------------------------
async def _create_with_retries(client: Any, kwargs: Dict[str, Any]) -> Any:
    """chat.completions.create with bounded retries.

    429: retried only while the summed Retry-After stays within GROQ_RATE_LIMIT_MAX_WAIT_SECONDS,
    otherwise LLMRateLimitedError (the client is told when to come back).
    Timeout: LLMUnavailableError at once (retrying would double an already long wait).
    5xx / connection error: retried after a short pause, then LLMUnavailableError.
    """
    from groq import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError  # type: ignore

    waited = 0.0
    retries = 0
    while True:
        try:
            return await client.chat.completions.create(**kwargs)
        except RateLimitError as exc:
            retry_after = _retry_after_seconds(exc)
            wait = retry_after if retry_after is not None else 1.0
            if retries >= settings.GROQ_RATE_LIMIT_MAX_RETRIES or waited + wait > settings.GROQ_RATE_LIMIT_MAX_WAIT_SECONDS:
                logger.warning("Groq rate limited; retry_after=%s s, giving up after %d retries", retry_after, retries)
                raise LLMRateLimitedError(retry_after) from exc
            logger.info("Groq rate limited; waiting %.1f s before retry %d", wait, retries + 1)
            retries += 1
            waited += wait
            await _sleep(wait)
        except APITimeoutError as exc:
            logger.warning("Groq request timed out after %.0f s", settings.GROQ_TIMEOUT_SECONDS)
            raise LLMUnavailableError() from exc
        except (APIConnectionError, InternalServerError) as exc:
            if retries >= settings.GROQ_RATE_LIMIT_MAX_RETRIES:
                logger.warning("Groq unavailable: %s", type(exc).__name__)
                raise LLMUnavailableError() from exc
            retries += 1
            await _sleep(_TRANSIENT_RETRY_DELAY_SECONDS)


async def _call_groq(
    messages: List[Dict[str, str]],
    *,
    response_format: Optional[Dict[str, str]] = None,
    temperature: float = 0.2,
    model_name: Optional[str] = None,
) -> str:
    """Call Groq API with prompt-hash caching.  Returns the assistant's text."""
    model = model_name or settings.GROQ_MODEL_NAME
    key = _cache_key(
        model,
        messages,
        temperature=temperature,
        response_format=response_format,
    )

    if key in _response_cache:
        _response_cache.move_to_end(key)
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

    completion = await _create_with_retries(client, kwargs)
    if not completion.choices:
        logger.warning("Groq completion returned empty choices; model=%s", model)
        return ""
    text: str = completion.choices[0].message.content or ""
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

NO_RELEVANT_LAW_ANSWER: str = (
    "Veritabanımızdaki mevzuat kapsamında bu sorunun doğrudan cevabı bulunamadı; "
    "lütfen bir hukuk uzmanına danışınız."
)

_QA_SYSTEM = """\
Sen Türk hukuku alanında uzman bir AI asistanısın.
Görevin, kullanıcının sorusuna SADECE aşağıda sana sağlanan kanun maddeleri bağlamında kalarak cevap vermektir.

KESİN KURALLAR:
1. SADAKAT (FAITHFULNESS): Yalnızca verilen kanun metinlerindeki bilgilere dayan. Kendi önceden eğitilmiş genel bilginden, varsayımlardan veya dış kaynaklardan kesinlikle hukuk kuralı veya bilgi uydurma (halüsinasyon yapma).
2. STANDART MADDE ATIFI: Cevabında dayandığın kanun ve madde numarasını HER ZAMAN açık ve standart bir biçimde zikret.
   - Standart format: "[Kanun Adı] Madde [No] uyarınca..." (Örn: "Türk Borçlar Kanunu Madde 344 uyarınca...", "Tüketicinin Korunması Hakkında Kanun Madde 11 uyarınca...", "İş Kanunu Madde 17 uyarınca...").
   - Kanun ve madde numarası belirtmeden soyut bir hukuki kural veya iddia öne sürme.
   - Yalnızca sana sunulan maddelere atıf yap; bağlamda yer almayan maddelere atıfta bulunma.
3. BİLGİ YETERSİZLİĞİ VE HALÜSİNASYON BARİYERİ:
   - Eğer kullanıcının sorusunun doğrudan ve kesin cevabı sağlanan kanun maddelerinde YOKSA veya maddeler bu konuyu açıklamaya YETMİYORSA, kesinlikle tahmin yürütme ya da genel ilkelerden cevap uydurma.
   - Bu durumda DOĞRUDAN ve YALNIZCA şu standart yanıtı ver:
     "Veritabanımızdaki mevzuat kapsamında bu sorunun doğrudan cevabı bulunamadı; lütfen bir hukuk uzmanına danışınız."
4. DİL VE ÜSLUP: Cevabını Türkçe, profesyonel, net, tarafsız ve anlaşılır yaz. Gereksiz dolambaçlı ifadelerden kaçın.
"""

_DOC_SYSTEM = """\
Sen Türk hukuku alanında uzman bir AI asistanısın.
Kullanıcının mesajından hukuki belge oluşturmak için gerekli OLAY PARAMETRELERİNİ çıkar.

ÖNEMLİ KVKK KURALLARI:
- KİŞİSEL VERİLERİ (PII) ASLA isteme ve missing_fields içine ASLA koyma.
- Yasaklı alan adları: kiraci_ad_soyad, kiraci_tc, kiraci_adres, kiraya_veren_ad_soyad,
  kiraya_veren_tc, kiraya_veren_adres, tasinmaz_adresi, tc, tc_kimlik, iban, ad_soyad, adres, telefon.
- Bu veriler ayrı bir güvenli form aracılığıyla toplanır; sen sadece olayı anlatan parametreleri çıkar.

Desteklenen şablon kimlikleri:
- "kira_ihtarname_temerrut"      : Kiracı ödeme yapmadığında ev sahibi adına temerrüt ihtarnamesi
- "tuketici_ayipli_mal_ihtarname": Ayıplı mal için tüketici şikayet/başvuru belgesi
- "kira_artis_itiraz_ihtarname"  : Kiraya verenin TBK m. 344'ü aşan fahiş kira artış talebine kiracının itirazı

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
    "olay_tarihi": "<YYYY-MM-DD|null>",
    "kira_baslangic_tarihi": "<YYYY-MM-DD|null>",
    "mevcut_kira_tutari": <number|null>,
    "talep_edilen_kira_tutari": <number|null>,
    "tufe_oran": <number|null>,
    "noter_ili": "<string|null>"
  },
  "missing_fields": ["<alan_adı>", ...]
}

missing_fields: Belgeyi oluşturmak için kullanıcıdan hâlâ öğrenilmesi gereken OLAY alanlarının listesi.
Eğer tüm alanlar mevcutsa boş liste döndür.
HATIRLATMA: missing_fields içine ASLA kişisel veri (tc, iban, ad_soyad, adres vb.) alanı koyma.
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
    },
    "missing_fields": ["odeme_suresi_gun"],
}

_MOCK_TUKETICI_DOC_PARAMS: Dict[str, Any] = {
    "suggested_template_id": "tuketici_ayipli_mal_ihtarname",
    "extracted_params": {
        "uyusmazlik_turu": "Ayıplı Mal",
        "urun_adi": "Elektronik Ürün",
        "satin_alma_tutari": 10000,
        "ayip_detayi": "Ürün arızalı",
    },
    "missing_fields": ["olay_tarihi"],
}

_MOCK_ARTIS_DOC_PARAMS: Dict[str, Any] = {
    "suggested_template_id": "kira_artis_itiraz_ihtarname",
    "extracted_params": {
        "mevcut_kira_tutari": 15000,
        "talep_edilen_kira_tutari": 30000,
        "tufe_oran": 48.0,
        "noter_ili": "İstanbul",
    },
    "missing_fields": ["kira_baslangic_tarihi"],
}

# ---------------------------------------------------------------------------
# Validation helpers (templates, PII stripping, citation grounding)
# ---------------------------------------------------------------------------

_ALLOWED_TEMPLATE_IDS = frozenset({
    "kira_ihtarname_temerrut",
    "tuketici_ayipli_mal_ihtarname",
    "kira_artis_itiraz_ihtarname",
})

_PII_FIELD_EXACT = frozenset({
    "tc",
    "tc_id",
    "tc_kimlik",
    "iban",
    "ad_soyad",
    "adres",
    "telefon",
    "email",
    "eposta",
    "e_posta",
    "banka_hesap_bilgisi",
    "tasinmaz_adresi",
    "kiralanan_tasinmaz_adresi",
})

_PII_FIELD_SUBSTRINGS = (
    "tc_kimlik",
    "tc_id",
    "_tc",
    "tc_",
    "iban",
    "ad_soyad",
    "adres",
    "telefon",
    "email",
    "eposta",
    "banka_hesap",
    "kiraci_",
    "kiraya_veren_",
)


def _is_pii_field(field_name: str) -> bool:
    """Return True if a field name refers to personal identifying information (KVKK)."""
    norm = field_name.replace("İ", "i").replace("I", "ı").lower().strip()
    if norm in _PII_FIELD_EXACT:
        return True
    return any(sub in norm for sub in _PII_FIELD_SUBSTRINGS)


_LAW_CODE_ALIASES: Dict[str, str] = {
    "tbk": "TBK",
    "türk borçlar kanunu": "TBK",
    "borçlar kanunu": "TBK",
    "6098": "TBK",
    "tkhk": "TKHK",
    "tüketicinin korunması hakkında kanun": "TKHK",
    "tüketici kanunu": "TKHK",
    "6502": "TKHK",
    "ik": "IK",
    "i̇k": "IK",
    "iş kanunu": "IK",
    "4857": "IK",
    "iik": "IIK",
    "i̇i̇k": "IIK",
    "icra ve iflas kanunu": "IIK",
    "2004": "IIK",
    "hmk": "HMK",
    "hukuk muhakemeleri kanunu": "HMK",
    "6100": "HMK",
    "tmk": "TMK",
    "türk medeni kanunu": "TMK",
    "4721": "TMK",
    "tck": "TCK",
    "türk ceza kanunu": "TCK",
    "5237": "TCK",
}


def _canonical_law_code(text: str) -> Optional[str]:
    """Map a law name, abbreviation, or statute number to a canonical code."""
    norm = text.replace("İ", "i").replace("I", "ı").lower().strip()
    for alias, code in _LAW_CODE_ALIASES.items():
        if alias in norm:
            return code
    return None


_LAW_PREFIX_PAT = (
    r"(?:"
    r"türk borçlar kanunu|borçlar kanunu|"
    r"tüketicinin korunması hakkında kanun|tüketici kanunu|"
    r"iş kanunu|icra ve iflas kanunu|hukuk muhakemeleri kanunu|"
    r"türk medeni kanunu|türk ceza kanunu|"
    r"tbk|tkhk|i̇k|ik|i̇i̇k|iik|hmk|tmk|tck|"
    r"6098|6502|4857|2004|6100|4721|5237"
    r")"
)
_CITE_KEYWORD_RE = re.compile(
    rf"(?:({_LAW_PREFIX_PAT})\s*(?:sayılı\s+kanun(?:'?un|'nın|un)?\s*)?)?\b(?:madde|md\.?|m\.?)\s*(\d+)\b"
)
_CITE_ORDINAL_RE = re.compile(
    rf"(?:({_LAW_PREFIX_PAT})\s*(?:sayılı\s+kanun(?:'?un|'nın|un)?\s*)?)?\b(\d+)\.\s*madd(?:e|esi|esine|eyi|ede|eden)\b"
)
_CITE_CODE_NUM_RE = re.compile(r"\b(tbk|tkhk|i̇k|ik|i̇i̇k|iik|hmk|tmk|tck)[-\s]+(\d+)\b")


def _validate_answer_citations(answer: str, valid_citations: List[Citation]) -> bool:
    """Verify the answer cites at least one retrieved article and no unretrieved articles."""
    retrieved_nums: Set[str] = set()
    retrieved_pairs: Set[Tuple[str, str]] = set()

    for c in valid_citations:
        nums = re.findall(r"\d+", c.article_id or "")
        law_code = _canonical_law_code(c.article_id or "") or _canonical_law_code(c.law_name or "")
        for num in nums:
            retrieved_nums.add(num)
            if law_code:
                retrieved_pairs.add((law_code, num))

    if not retrieved_nums:
        return False

    norm_answer = answer.replace("İ", "i").replace("I", "ı").lower()
    found_citations: List[Tuple[Optional[str], str]] = []

    for pat in (_CITE_KEYWORD_RE, _CITE_ORDINAL_RE, _CITE_CODE_NUM_RE):
        for match in pat.finditer(norm_answer):
            raw_law, num = match.group(1), match.group(2)
            law_code = _canonical_law_code(raw_law) if raw_law else None
            found_citations.append((law_code, num))

    if not found_citations:
        return False

    for law_code, num in found_citations:
        if num not in retrieved_nums:
            return False
        if law_code and retrieved_pairs and (law_code, num) not in retrieved_pairs:
            # Only reject on law mismatch if retrieved_pairs has entries for this article number
            if any(pair_num == num for _, pair_num in retrieved_pairs):
                return False

    return True


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
            return self._mock_response(cleaned_message, retrieved_citations)

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
        response_format = {"type": "json_object"}
        raw = await _call_groq(
            messages,
            response_format=response_format,
            temperature=0.0,
            model_name=self.model_name,
        )

        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                logger.warning("Intent classification JSON is not a dict; raw=%s", str(raw)[:200])
                return "out_of_scope"
            intent_value = data.get("intent", "out_of_scope")
            if intent_value in ("question_answering", "document_generation", "out_of_scope"):
                _cache_set(
                    _cache_key(
                        self.model_name,
                        messages,
                        temperature=0.0,
                        response_format=response_format,
                    ),
                    raw,
                )
                return intent_value  # type: ignore[return-value]
        except (json.JSONDecodeError, TypeError, AttributeError):
            logger.warning("Intent classification JSON parse failed; raw=%s", str(raw)[:200])

        return "out_of_scope"

    # ------------------------------------------------------------------
    # Step 2a: RAG-grounded legal Q&A
    # ------------------------------------------------------------------

    async def _answer_legal_question(
        self, message: str, citations: List[Citation]
    ) -> str:
        """Generate a strictly RAG-grounded Turkish legal answer."""
        valid_citations = [
            c for c in citations
            if c.text_snippet and c.text_snippet.strip()
        ]
        if not valid_citations:
            return NO_RELEVANT_LAW_ANSWER

        # Build context block from retrieved articles (deduplicating identical article excerpts)
        seen_snippets = set()
        context_parts: List[str] = []
        for c in valid_citations:
            snippet_cleaned = c.text_snippet.strip()
            key = (c.article_id, snippet_cleaned)
            if key in seen_snippets:
                continue
            seen_snippets.add(key)
            context_parts.append(
                f"[{c.article_id}] {c.law_name}:\n{snippet_cleaned}"
            )
        context_block = "\n\n---\n\n".join(context_parts)

        messages = [
            {"role": "system", "content": _QA_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Kanun maddeleri:\n{context_block}\n\n"
                    f"Kullanıcı sorusu: {message.strip()}"
                ),
            },
        ]
        answer = await _call_groq(messages, temperature=0.1, model_name=self.model_name)
        stripped = answer.strip()
        if not stripped:
            return NO_RELEVANT_LAW_ANSWER

        if stripped == NO_RELEVANT_LAW_ANSWER:
            _cache_set(_cache_key(self.model_name, messages, temperature=0.1), stripped)
            return stripped

        if not _validate_answer_citations(stripped, valid_citations):
            logger.warning("Rejected Q&A answer failing citation grounding check.")
            return NO_RELEVANT_LAW_ANSWER

        _cache_set(_cache_key(self.model_name, messages, temperature=0.1), stripped)
        return stripped

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
        response_format = {"type": "json_object"}
        raw = await _call_groq(
            messages,
            response_format=response_format,
            temperature=0.0,
            model_name=self.model_name,
        )

        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                logger.warning("Doc param extraction JSON is not a dict; raw=%s", str(raw)[:200])
                return "kira_ihtarname_temerrut", {}, ["uyusmazlik_turu", "kira_tutari"]

            raw_template_id = data.get("suggested_template_id")
            template_id: str = (
                raw_template_id
                if isinstance(raw_template_id, str) and raw_template_id in _ALLOWED_TEMPLATE_IDS
                else "kira_ihtarname_temerrut"
            )

            raw_params = data.get("extracted_params")
            if isinstance(raw_params, dict):
                extracted_params: Dict[str, Any] = {
                    str(k): v
                    for k, v in raw_params.items()
                    if v is not None and not _is_pii_field(str(k))
                }
            else:
                extracted_params = {}

            raw_missing = data.get("missing_fields")
            if isinstance(raw_missing, list):
                missing_fields: List[str] = [
                    str(f)
                    for f in raw_missing
                    if f is not None and str(f).strip() and not _is_pii_field(str(f))
                ]
            else:
                missing_fields = []

            _cache_set(
                _cache_key(
                    self.model_name,
                    messages,
                    temperature=0.0,
                    response_format=response_format,
                ),
                raw,
            )
            return template_id, extracted_params, missing_fields
        except (json.JSONDecodeError, TypeError, AttributeError):
            logger.warning("Doc param extraction JSON parse failed; raw=%s", str(raw)[:200])
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
            "kira_artis_itiraz_ihtarname": "Fahiş Kira Artışına İtiraz İhtarnamesi",
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
        self,
        message: str,
        citations: Optional[List[Citation]] = None,
    ) -> Tuple[
        Literal["question_answering", "document_generation", "out_of_scope"],
        str,
        Dict[str, Any],
        List[str],
        Optional[str],
    ]:
        """Return deterministic mock responses when no real Groq key is present."""
        # Turkish uppercase normalization: İ->i, I->ı
        lowered = message.replace("İ", "i").replace("I", "ı").lower()

        out_of_scope_re = re.compile(
            r"\b(hava durumu|hava nasıl|yemek tarifi|futbol|maç sonucu|ceza davası|boşanma|vergi|kripto)\b"
        )
        if out_of_scope_re.search(lowered):
            return (
                "out_of_scope",
                "⚠️ [MOCK MOD] Bu konuda yardımcı olamıyorum. Yalnızca kira hukuku, tüketici hukuku, "
                "iş hukuku ve genel borçlar hukuku kapsamındaki sorularınızda ve yasal belge "
                "taleplerinizde destek sunabiliyorum.",
                {},
                [],
                None,
            )

        doc_noun_re = re.compile(r"\b(ihtarname\w*|dilekçe\w*|belge\w*|başvuru\w*)\b")
        doc_action_re = re.compile(
            r"\b(hazırla\w*|oluştur\w*|düzenle\w*|yazdır\w*|yaz|üret\w*|göndermemi istedi)\b"
        )
        is_question = "?" in lowered and bool(
            re.search(r"\b(nedir|nasıl|ne olur|şartları|gerekir|mı|mi|mu|mü)\b", lowered)
        )

        if doc_noun_re.search(lowered) and doc_action_re.search(lowered) and not is_question:
            if any(kw in lowered for kw in ("ayıplı", "bozuk", "arızalı", "tüketici", "ürün")):
                mock = _MOCK_TUKETICI_DOC_PARAMS
            elif any(kw in lowered for kw in ("artış", "itiraz", "zam", "fahiş", "tüfe")):
                mock = _MOCK_ARTIS_DOC_PARAMS
            else:
                mock = _MOCK_DOC_PARAMS
            return (
                "document_generation",
                "⚠️ [MOCK MOD] " + self._doc_answer(
                    mock["suggested_template_id"],
                    mock["extracted_params"],
                    mock["missing_fields"],
                ),
                mock["extracted_params"],
                mock["missing_fields"],
                mock["suggested_template_id"],
            )
        if citations is not None and not any(c.text_snippet and c.text_snippet.strip() for c in citations):
            return "question_answering", f"⚠️ [MOCK MOD] {NO_RELEVANT_LAW_ANSWER}", {}, [], None

        return "question_answering", _MOCK_QA_ANSWER, {}, [], None


# ---------------------------------------------------------------------------
# Singleton instance (imported by chat.py router)
# ---------------------------------------------------------------------------
llm_service = LLMService()
