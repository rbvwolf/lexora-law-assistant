"""ChromaDB ingestion CLI for article-based Turkish statutory corpora.

Reads structured law JSON files from `data/laws/*.json`, computes multilingual embeddings
(using multilingual-e5 or mpnet), and upserts chunks into ChromaDB with required metadata.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.config import format_passage, settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Expected law JSON files in data/laws/
EXPECTED_LAW_FILES = [
    "tbk_kira.json",
    "tkhk_tuketici.json",
    "tbk_temerrut.json",
    "ik_is.json",
]


def load_law_json(json_path: Path) -> List[Dict[str, Any]]:
    """Load and validate an article-based law JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected list of articles in {json_path}, got {type(data)}")
    return data


def format_article_content(article: Dict[str, Any]) -> str:
    """Format full statutory article representation for embedding and retrieval."""
    law = article.get("law", "").strip()
    article_no = article.get("article_no", "")
    title = article.get("title", "").strip()
    body = article.get("text", "").strip()

    if title:
        header = f"{law} Madde {article_no} ({title}):"
    else:
        header = f"{law} Madde {article_no}:"

    return f"{header}\n{body}"


def ingest_laws(
    data_dir: Path,
    persist_dir: Path,
    model_name: str,
    collection_name: str = "legal_articles",
    reset_collection: bool = False,
) -> int:
    """Ingest law JSON files into persistent ChromaDB collection.

    Returns:
        int: Total number of ingested articles in the collection.
    """
    logger.info(f"Connecting to persistent ChromaDB at: {persist_dir.resolve()}")
    client = chromadb.PersistentClient(path=str(persist_dir.resolve()))

    if reset_collection:
        try:
            client.delete_collection(name=collection_name)
            logger.info(f"Deleted existing collection '{collection_name}' for clean re-indexing.")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)

    all_ids: List[str] = []
    all_documents: List[str] = []
    all_passages: List[str] = []
    all_metadatas: List[Dict[str, Any]] = []
    seen_ids = set()

    files_found = 0
    for filename in EXPECTED_LAW_FILES:
        filepath = data_dir / filename
        if not filepath.exists():
            logger.warning(f"Expected law file not found: {filepath}")
            continue

        articles = load_law_json(filepath)
        files_found += 1
        logger.info(f"Processing {filename} ({len(articles)} articles)...")

        for art in articles:
            article_id = str(art["article_id"])
            if article_id in seen_ids:
                raise ValueError(f"Duplicate article_id '{article_id}' found in {filepath}")
            seen_ids.add(article_id)

            raw_article_no = art.get("article_no")
            if isinstance(raw_article_no, bool) or not (
                isinstance(raw_article_no, int)
                or isinstance(raw_article_no, str)
            ):
                raise ValueError(
                    f"Invalid article_no for article '{article_id}' in {filepath}: "
                    f"{raw_article_no!r}"
                )
            try:
                article_no = int(raw_article_no)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid article_no for article '{article_id}' in {filepath}: "
                    f"{raw_article_no!r}"
                ) from exc
            if article_no <= 0:
                raise ValueError(
                    f"Invalid article_no for article '{article_id}' in {filepath}: "
                    f"{raw_article_no!r}"
                )

            content = format_article_content(art)
            passage = format_passage(content, model_name=model_name)

            metadata = {
                "article_id": article_id,
                "law": str(art.get("law", "")),
                "article_no": article_no,
                "title": str(art.get("title") or ""),
                "domain": str(art.get("domain") or ""),
            }

            all_ids.append(article_id)
            all_documents.append(content)
            all_passages.append(passage)
            all_metadatas.append(metadata)

    if not all_ids:
        logger.error(f"No articles found to ingest in {data_dir.resolve()}")
        return 0

    logger.info(f"Computing embeddings for {len(all_passages)} statutory articles...")
    embeddings = model.encode(
        all_passages,
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=32,
    ).tolist()

    logger.info(f"Upserting {len(all_ids)} articles into collection '{collection_name}'...")
    collection.upsert(
        ids=all_ids,
        documents=all_documents,
        embeddings=embeddings,
        metadatas=all_metadatas,
    )

    if not reset_collection and files_found == len(EXPECTED_LAW_FILES):
        existing_ids = set(collection.get(include=[])["ids"])
        orphan_ids = list(existing_ids - set(all_ids))
        if orphan_ids:
            logger.info(f"Pruning {len(orphan_ids)} obsolete/orphan articles from collection: {orphan_ids}")
            collection.delete(ids=orphan_ids)

    total_count = collection.count()
    logger.info(
        f"Ingestion complete: {len(all_ids)} articles from {files_found} files upserted. "
        f"Total count in '{collection_name}': {total_count}"
    )
    return total_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Turkish law JSON corpora into ChromaDB.")
    project_root = Path(__file__).resolve().parent.parent.parent
    default_data_dir = project_root / "data" / "laws"
    configured_persist_dir = Path(settings.CHROMA_PERSIST_DIR)
    default_persist_dir = (
        configured_persist_dir
        if configured_persist_dir.is_absolute()
        else project_root / configured_persist_dir
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_data_dir,
        help="Directory containing structured law JSON files (default: data/laws)",
    )
    parser.add_argument(
        "--persist-dir",
        type=Path,
        default=default_persist_dir,
        help="Directory where ChromaDB persists data (default: from settings.CHROMA_PERSIST_DIR)",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default=settings.EMBEDDING_MODEL_NAME,
        help="Embedding model name (default: from settings.EMBEDDING_MODEL_NAME)",
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default="legal_articles",
        help="Name of the ChromaDB collection (default: legal_articles)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset/re-create the collection before inserting",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    total = ingest_laws(
        data_dir=args.data_dir,
        persist_dir=args.persist_dir,
        model_name=args.model_name,
        collection_name=args.collection_name,
        reset_collection=args.reset,
    )
    if total == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
