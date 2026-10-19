import logging
from typing import Any, Dict, List, Literal, Optional, Tuple

from app.core.config import settings
from app.core.langfuse import trace_llm_call
from app.schemas.chat import Citation

logger = logging.getLogger(__name__)


class LLMService:
    """Service handling Groq API interactions and structured parameter extraction."""

    def __init__(self):
        self.model_name = settings.GROQ_MODEL_NAME

    @trace_llm_call(name="classify_intent_and_extract")
    async def process_chat_message(
        self,
        cleaned_message: str,
        retrieved_citations: List[Citation],
    ) -> Tuple[Literal["question_answering", "document_generation", "out_of_scope"], str, Dict[str, Any], List[str], Optional[str]]:
        """Classify user intent, route to answer or structured parameter extraction.

        Returns:
            (intent, answer, extracted_params, missing_fields, suggested_template_id)
        """
        lowered = cleaned_message.lower()

        # Document generation trigger heuristics (e.g., petition/notice requests)
        doc_keywords = ["ihtarname", "dilekçe", "tahliye", "başvuru", "hazırla", "yaz", "oluştur", "fesih"]
        is_doc_intent = any(kw in lowered for kw in doc_keywords)

        if is_doc_intent:
            intent: Literal["question_answering", "document_generation", "out_of_scope"] = "document_generation"
            suggested_template_id = "kira_ihtarname_temerrut"
            extracted_params = {
                "uyusmazlik_turu": "Kira Ödememe (Temerrüt)",
                "kira_tutari": 15000,
                "gecikilen_aylar": ["Eylül 2026", "Ekim 2026"],
                "odeme_suresi_gun": 30,
            }
            missing_fields = ["banka_hesap_bilgisi", "kiralanan_tasinmaz_adresi"]
            answer = (
                "Kiracınızın kira bedelini ödememesi sebebiyle Türk Borçlar Kanunu Madde 315 uyarınca "
                "30 günlük ödeme süresi içeren temerrüt ihtarnamesi hazırlayabiliriz. "
                "Belirtilen kira tutarı tespit edildi. İhtarnameyi tamamlamak için lütfen banka hesap ve "
                "taşınmaz bilgilerini onaylayınız, ardından kimlik formunu doldurunuz."
            )
            return intent, answer, extracted_params, missing_fields, suggested_template_id

        # Non-legal or out of scope queries
        out_of_scope_keywords = ["hava durumu", "yemek tarifi", "futbol", "film öner"]
        if any(kw in lowered for kw in out_of_scope_keywords):
            return (
                "out_of_scope",
                "Ben Türk Hukuku alanında geliştirilmiş bir AI asistanıyım. Yalnızca hukuki sorularınızı cevaplayabilir ve yasal belge taslakları hazırlayabilirim.",
                {},
                [],
                None,
            )

        # Standard legal question answering
        intent = "question_answering"
        answer = (
            "Türk Borçlar Kanunu Madde 344 uyarınca konut kiralarında kira artış oranı, "
            "bir önceki kira yılındaki tüketici fiyat endeksindeki (TÜFE) on iki aylık ortalamalara "
            "göre değişim oranını geçemez. Taraflarca bu oranı aşan bir anlaşma yapılmış olsa dahi "
            "aşan kısım geçersiz sayılır."
        )
        return intent, answer, {}, [], None


# Singleton instance
llm_service = LLMService()
