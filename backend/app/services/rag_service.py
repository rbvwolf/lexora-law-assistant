"""RAG service managing ChromaDB vector retrieval with article-based Turkish statutory chunking.

Provides semantic search over statutory law articles (TBK, TKHK, İş Kanunu, etc.)
with automatic prefixing for multilingual-e5 models and optional domain filtering.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

from app.core.config import format_query, settings
from app.core.thesaurus import legal_thesaurus
from app.schemas.chat import Citation

logger = logging.getLogger(__name__)


class RAGService:
    """Service managing persistent ChromaDB vector retrieval with article-based chunking."""

    _instance: Optional["RAGService"] = None

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        model_name: Optional[str] = None,
        collection_name: str = "legal_articles",
    ):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.collection_name = collection_name

        self._client: Optional[chromadb.PersistentClient] = None
        self._collection: Optional[Any] = None
        self._model: Optional[SentenceTransformer] = None

    @classmethod
    def get_instance(cls) -> "RAGService":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_client(self) -> chromadb.PersistentClient:
        """Lazy load persistent ChromaDB client."""
        if self._client is None:
            # Resolve relative persist_dir against project root or current working directory
            p = Path(self.persist_dir)
            if not p.is_absolute():
                candidate = Path.cwd() / p
                if candidate.exists() or (Path.cwd() / "data").exists():
                    p = candidate
                else:
                    project_root = Path(__file__).resolve().parent.parent.parent.parent
                    p = project_root / self.persist_dir.lstrip("./")

            logger.info(f"Connecting RAGService to ChromaDB at: {p.resolve()}")
            self._client = chromadb.PersistentClient(path=str(p.resolve()))
        return self._client

    def _get_collection(self):
        """Lazy load the target ChromaDB collection."""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _get_model(self) -> SentenceTransformer:
        """Lazy load and cache SentenceTransformer embedding model."""
        if self._model is None:
            logger.info(f"Loading embedding model for RAG retrieval: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def retrieve_articles(
        self,
        query: str,
        top_k: int = 5,
        domain_filter: Optional[str] = None,
    ) -> List[Citation]:
        """Perform semantic search on article-based ChromaDB collection and return statutory citations.

        Args:
            query: User's legal question or case statement.
            top_k: Maximum number of articles to retrieve (default: 5).
            domain_filter: Optional domain constraint (e.g., 'kira_hukuku', 'tuketici_hukuku').

        Returns:
            List[Citation]: Ranked list of statutory citations with article_id, law_name, and text snippet.
        """
        if not isinstance(query, str) or not query.strip():
            logger.warning("Empty or invalid query passed to retrieve_articles.")
            return []

        if top_k <= 0:
            logger.warning(f"Non-positive top_k ({top_k}) passed to retrieve_articles.")
            return []

        collection = self._get_collection()
        total_docs = collection.count()
        if total_docs == 0:
            logger.warning(f"ChromaDB collection '{self.collection_name}' is empty. Returning 0 citations.")
            return []

        # Expand query using legal thesaurus to bridge colloquial terminology gaps
        expanded_q = legal_thesaurus.expand_query(query)

        # multilingual-e5 requires 'query: ' prefix; mpnet uses raw query
        formatted_q = format_query(expanded_q.strip(), model_name=self.model_name)
        model = self._get_model()
        query_embedding = model.encode([formatted_q], normalize_embeddings=True).tolist()

        where_clause: Optional[Dict[str, Any]] = None
        if domain_filter and isinstance(domain_filter, str) and domain_filter.strip():
            where_clause = {"domain": domain_filter.strip()}

        effective_k = min(top_k, total_docs)
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=effective_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"],
        )

        citations: List[Citation] = []
        ids_list = results.get("ids", [[]])[0]
        metadatas_list = results.get("metadatas", [[]])[0]
        documents_list = results.get("documents", [[]])[0]

        for i, article_id in enumerate(ids_list):
            meta = metadatas_list[i] if i < len(metadatas_list) and metadatas_list[i] else {}
            doc_text = documents_list[i] if i < len(documents_list) and documents_list[i] else ""

            # Extract clean snippet from doc_text or metadata
            law_name = meta.get("law", "")
            article_id_str = meta.get("article_id", article_id)

            citations.append(
                Citation(
                    article_id=article_id_str,
                    law_name=law_name,
                    text_snippet=doc_text,
                )
            )

        logger.info(
            f"Retrieved {len(citations)} citations for query: {query[:40]}... "
            f"(domain_filter={domain_filter})"
        )
        return citations

    async def retrieve_citations(
        self,
        query: str,
        top_k: int = 5,
        domain_filter: Optional[str] = None,
    ) -> List[Citation]:
        """Async entrypoint for API routes (such as /api/v1/chat/message)."""
        return self.retrieve_articles(query=query, top_k=top_k, domain_filter=domain_filter)


# Singleton instance
rag_service = RAGService()
