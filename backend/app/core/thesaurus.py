"""Legal thesaurus for bridging colloquial Turkish language gaps to statutory terminology.

Maps informal terms (e.g. 'depozito', 'maaş', 'oğlum') to canonical Turkish legal
statutory concepts (e.g. 'güvence', 'ücret', 'altsoyu') without hardcoding
any specific article numbers or laws.
"""

import re
from typing import List, Tuple


class LegalThesaurus:
    """Thesaurus providing targeted vocabulary expansion for Turkish legal queries."""

    # Pairs of (compiled regex pattern, statutory concept replacement/expansion)
    # Note: Article IDs/numbers are NEVER hardcoded here.
    CONCEPT_MAPPINGS: List[Tuple[re.Pattern, str]] = [
        # Rental Law terminology gaps
        (re.compile(r"\bdepozito\w*\b", re.IGNORECASE), "güvence bedeli"),
        (re.compile(r"\boğl(um|uma|umu|unun|umun)?\b", re.IGNORECASE), "altsoyu"),
        (re.compile(r"\bkız(ım|ıma|ımı|ımın|lar|ları)?\b", re.IGNORECASE), "altsoyu"),
        (re.compile(r"\bann(em|eme|emi|emin|emle)?\b", re.IGNORECASE), "üstsoyu"),
        (re.compile(r"\bbab(am|ama|amı|amın|amla)?\b", re.IGNORECASE), "üstsoyu"),
        (re.compile(r"\btorun(um|uma|umu|unun|umun)?\b", re.IGNORECASE), "altsoyu"),
        # Rental Law: Rent increase / limitation gaps (TBK 344)
        (re.compile(r"\bkira\w*\s+([^.!?]*\s+)?(art[ıi]r\w*|zam\w*|artı(ş|şı|şları))\b", re.IGNORECASE), "kira bedelinin belirlenmesi artış oranı tüketici fiyat endeksi tüfe"),
        (re.compile(r"\bkiray[ıi]\s+([^.!?]*\s+)?art[ıi]r\w*\b", re.IGNORECASE), "kira bedelinin belirlenmesi artış oranı tüketici fiyat endeksi tüfe"),
        (re.compile(r"(%|\byüzde\s*)\s*\d+\s*(zam|art[ıi]r|artış)", re.IGNORECASE), "kira bedelinin belirlenmesi artış oranı tüketici fiyat endeksi tüfe"),
        # Labor Law terminology gaps
        (re.compile(r"\bmaaş\w*\b", re.IGNORECASE), "ücret"),
        (re.compile(r"\bfazla mesai\w*\b", re.IGNORECASE), "fazla çalışma ücreti"),
        (re.compile(r"\bişten (atılma|atıldım|çıkarılma|çıkarıldım|kovulma|kovuldum)\b", re.IGNORECASE), "iş sözleşmesinin feshi"),
        # Consumer Law terminology gaps
        (re.compile(r"\b(bozuk|arızalı|hatalı) (mal|ürün|eşya|telefon|cihaz|araba|bilgisayar|televizyon)\b", re.IGNORECASE), "ayıplı mal"),
        (re.compile(r"\b(bozuk|arızalı|hatalı) çıktı\b", re.IGNORECASE), "ayıplı mal"),
        (re.compile(r"\bpara iadesi\b", re.IGNORECASE), "sözleşmeden dönme bedel iadesi"),
        # Default / Debt terminology gaps
        (re.compile(r"\bborcu(nu)? ödemiyor\b", re.IGNORECASE), "borçlunun temerrüdü"),
    ]

    def expand_query(self, query: str) -> str:
        """Expand user query with statutory concepts where colloquial gaps exist.

        Args:
            query: User's raw question or statement.

        Returns:
            str: Original query augmented with relevant statutory concepts in parentheses.
        """
        if not query or not query.strip():
            return ""

        original = query.strip()
        expansions = []

        for pattern, statutory_concept in self.CONCEPT_MAPPINGS:
            if pattern.search(original):
                if statutory_concept not in expansions and statutory_concept.lower() not in original.lower():
                    expansions.append(statutory_concept)

        if not expansions:
            return original

        # Append statutory concepts cleanly at the end
        return f"{original} ({' '.join(expansions)})"


legal_thesaurus = LegalThesaurus()
