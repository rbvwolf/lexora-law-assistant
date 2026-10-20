"""Parser script to convert raw Turkish statutory texts into structured article-based JSON files.

Reads raw .txt law files from `data/laws/raw_txts/`, extracts article metadata,
cleans formatting and footnote artifacts, and exports JSON to `data/laws/`.
"""

import argparse
import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Registry of known statutory documents with their metadata
LAW_REGISTRY: Dict[str, Dict[str, Any]] = {
    "tbk_kira.txt": {
        "law_name": "6098 Sayılı Türk Borçlar Kanunu",
        "article_prefix": "TBK",
        "domain": "kira_hukuku",
        "output_filename": "tbk_kira.json",
    },
    "tkhk_tuketici.txt": {
        "law_name": "6502 Sayılı Tüketicinin Korunması Hakkında Kanun",
        "article_prefix": "TKHK",
        "domain": "tuketici_hukuku",
        "output_filename": "tkhk_tuketici.json",
    },
    "tbk_temerrut.txt": {
        "law_name": "6098 Sayılı Türk Borçlar Kanunu",
        "article_prefix": "TBK",
        "domain": "borclar_genel",
        "output_filename": "tbk_temerrut.json",
    },
    "ik_is.txt": {
        "law_name": "4857 Sayılı İş Kanunu",
        "article_prefix": "IK",
        "domain": "is_hukuku",
        "output_filename": "ik_is.json",
    },
}

# Known structural sections or division headings to exclude from article titles
STRUCTURAL_SECTIONS = {
    "genel hükümler",
    "konut ve çatılı işyeri kiraları",
    "ayıplı mallar",
    "ayıplı hizmetler",
}

GENERIC_TITLE_PARTS = {
    "genel olarak",
    "şekil",
    "konusu",
    "kiraya veren tarafından",
    "kiracı tarafından",
}


@dataclass
class LawArticle:
    """Represents a single parsed statutory article with its metadata."""

    article_id: str
    law: str
    article_no: int
    title: str
    domain: str
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def is_heading_line(line: str) -> bool:
    """Check if a line matches typical Turkish legal heading patterns.

    Headings in Turkish legislation never end with punctuation like '.' or ';',
    while substantive sentences and sub-clauses in article bodies always do.
    """
    line = line.strip()
    if not line:
        return False

    # Remove footnote markers like [2], 2[3][4] or trailing digits
    cleaned = re.sub(r"\[\d+\]", "", line)
    cleaned = re.sub(r"(?<=[a-zA-ZçğıöşüÇĞİÖŞÜ])\d+$", "", cleaned).strip()

    # If line ends with period or semicolon, it's a substantive sentence or sub-clause, not a title
    if cleaned.endswith((".", ";")):
        return False

    # Part/Chapter markers (BİRİNCİ AYIRIM, İKİNCİ BÖLÜM, etc.)
    if re.match(r"^(BİRİNCİ|İKİNCİ|ÜÇÜNCÜ|DÖRDÜNCÜ|BEŞİNCİ)\s+(AYIRIM|BÖLÜM|KISIM)", cleaned, re.IGNORECASE):
        return True

    # Standalone structural section headers
    if cleaned.lower() in STRUCTURAL_SECTIONS:
        return True

    # Letter headings: 'A. Tanımı', 'B. Kira süresi', 'B. Borçlunun temerrüdü'
    if re.match(r"^[A-ZÇĞİÖŞÜ]\.\s+", cleaned):
        return True

    # Roman numeral headings: 'I. Teslim borcu', 'II. Hükümleri', 'I- Sağlık sebepleri'
    if re.match(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)[\.-]\s+", cleaned):
        return True

    # Digit headings: '1. Genel olarak', '2. İfa zamanı'
    if re.match(r"^\d+\.\s+", cleaned):
        return True

    # Sub-letter headings: 'a. Şekil', 'b. Aile konutu', 'a. Gecikme tazminatı'
    if re.match(r"^[a-zçğıöşü]\.\s+", cleaned):
        return True

    # Standalone unnumbered short title lines (e.g., 'Süreli fesih', 'Ayıplı mal', 'Zamanaşımı')
    if (
        len(cleaned) < 90
        and not re.match(r"^\(\d+\)|^[a-zçğıöşü]\)", cleaned)
        and not cleaned.endswith((":", ","))
    ):
        return True

    return False


def clean_title_part(h: str) -> str:
    """Clean numbering prefixes and footnote markers from a heading component."""
    h = h.strip()
    # Strip footnote brackets like [2], [3][4]
    h = re.sub(r"\[\d+\]", "", h)
    # Strip footnote trailing numbers attached to words, e.g. 'yasağı2' -> 'yasağı'
    h = re.sub(r"(?<=[a-zA-ZçğıöşüÇĞİÖŞÜ])\d+$", "", h)
    # Strip prefixes like 'A. ', 'I. ', 'I- ', '1. ', 'a. '
    h = re.sub(r"^[A-ZÇĞİÖŞÜ]\.\s*", "", h)
    h = re.sub(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)[\.-]\s*", "", h)
    h = re.sub(r"^\d+\.\s*", "", h)
    h = re.sub(r"^[a-zçğıöşü]\.\s*", "", h)
    return h.strip()


def format_article_title(raw_headings: List[str]) -> str:
    """Compose a clean, informative article title from raw heading lines."""
    # Filter out broad division markers
    filtered = [
        h for h in raw_headings
        if not re.match(r"^(BİRİNCİ|İKİNCİ|ÜÇÜNCÜ|DÖRDÜNCÜ|BEŞİNCİ)\s+(AYIRIM|BÖLÜM|KISIM)", h, re.IGNORECASE)
        and h.strip().lower() not in STRUCTURAL_SECTIONS
    ]
    if not filtered:
        return ""

    cleaned_parts = [clean_title_part(h) for h in filtered if clean_title_part(h)]
    if not cleaned_parts:
        return ""

    # If the deepest heading is generic (e.g. 'Genel olarak'), combine with its parent
    if len(cleaned_parts) > 1 and cleaned_parts[-1].lower() in GENERIC_TITLE_PARTS:
        return f"{cleaned_parts[-2]} - {cleaned_parts[-1]}"

    return cleaned_parts[-1]


def clean_article_body(raw_body: str) -> str:
    """Clean whitespace, remove footnote references, and normalize paragraphs in the article body."""
    # Strip bracketed footnote references like [6], [7] from text
    cleaned_body = re.sub(r"\[\d+\]", "", raw_body)

    raw_paragraphs = cleaned_body.split("\n")
    cleaned_paragraphs: List[str] = []

    current_para: List[str] = []
    for line in raw_paragraphs:
        stripped = " ".join(line.split())
        if stripped:
            current_para.append(stripped)
        else:
            if current_para:
                cleaned_paragraphs.append(" ".join(current_para))
                current_para = []

    if current_para:
        cleaned_paragraphs.append(" ".join(current_para))

    return "\n\n".join(cleaned_paragraphs)


def parse_law_content(
    content: str,
    law_name: str,
    article_prefix: str,
    domain: str,
) -> List[LawArticle]:
    """Parse raw text content of a law file into structured LawArticle models."""
    normalized_content = content.replace("\r\n", "\n")

    # Case-insensitive match for MADDE / Madde with hyphen or dash
    pattern = r"(?mi)^MADDE\s+(\d+)\s*[-–—:]\s*"
    matches = list(re.finditer(pattern, normalized_content))

    if not matches:
        logger.warning(f"No articles found matching pattern 'MADDE X-' for law: {law_name}")
        return []

    # Step 1: Collect preceding heading lines for each article
    article_headings: List[List[str]] = []
    for i, m in enumerate(matches):
        prev_end = matches[i - 1].end() if i > 0 else 0
        curr_start = m.start()
        interim = normalized_content[prev_end:curr_start]
        lines = [line.strip() for line in interim.split("\n") if line.strip()]

        if i == 0:
            h_lines = lines
        else:
            h_idx = len(lines)
            while h_idx > 0 and is_heading_line(lines[h_idx - 1]):
                h_idx -= 1
            h_lines = lines[h_idx:]

        article_headings.append(h_lines)

    # Step 2: Extract article text and construct LawArticle objects
    articles: List[LawArticle] = []
    for i, m in enumerate(matches):
        art_no = int(m.group(1))
        art_id = f"{article_prefix}-{art_no}"
        title = format_article_title(article_headings[i])

        body_start = m.end()
        if i + 1 < len(matches):
            next_start = matches[i + 1].start()
            interim = normalized_content[body_start:next_start]
            interim_lines = interim.split("\n")

            # Exclude the trailing heading lines that belong to the next article
            next_h_count = len(article_headings[i + 1])
            body_lines: List[str] = []
            h_counted = 0
            for line in reversed(interim_lines):
                if h_counted < next_h_count and line.strip():
                    h_counted += 1
                elif h_counted >= next_h_count:
                    body_lines.append(line)
            body_lines.reverse()
            raw_body = "\n".join(body_lines)
        else:
            raw_body = normalized_content[body_start:]

        cleaned_text = clean_article_body(raw_body)

        articles.append(
            LawArticle(
                article_id=art_id,
                law=law_name,
                article_no=art_no,
                title=title,
                domain=domain,
                text=cleaned_text,
            )
        )

    return articles


def parse_file(
    file_path: Path,
    law_name: str,
    article_prefix: str,
    domain: str,
) -> List[LawArticle]:
    """Read a raw law text file and parse it into LawArticle models."""
    logger.info(f"Reading raw file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    articles = parse_law_content(
        content=content,
        law_name=law_name,
        article_prefix=article_prefix,
        domain=domain,
    )
    logger.info(f"Successfully parsed {len(articles)} articles from {file_path.name}")
    return articles


def save_articles_to_json(articles: List[LawArticle], output_path: Path) -> None:
    """Save parsed articles to a UTF-8 encoded JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = [art.to_dict() for art in articles]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(articles)} articles to {output_path}")


def parse_and_export_all(
    raw_dir: Path,
    out_dir: Path,
    target_file: Optional[str] = None,
) -> Dict[str, List[LawArticle]]:
    """Parse registered law text files and export to JSON."""
    results: Dict[str, List[LawArticle]] = {}

    for filename, config in LAW_REGISTRY.items():
        if target_file and target_file != filename:
            continue

        raw_file = raw_dir / filename
        if not raw_file.exists():
            logger.warning(f"Raw law file not found: {raw_file}")
            continue

        articles = parse_file(
            file_path=raw_file,
            law_name=config["law_name"],
            article_prefix=config["article_prefix"],
            domain=config["domain"],
        )

        out_file = out_dir / config["output_filename"]
        save_articles_to_json(articles, out_file)
        results[filename] = articles

    return results


def main() -> None:
    """CLI entrypoint for parsing raw Turkish law text files."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    default_raw_dir = repo_root / "data" / "laws" / "raw_txts"
    default_out_dir = repo_root / "data" / "laws"

    parser = argparse.ArgumentParser(
        description="Parse raw Turkish law text files into structured article-based JSON."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=default_raw_dir,
        help="Directory containing raw .txt law files.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=default_out_dir,
        help="Directory where structured .json files will be exported.",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Specific raw filename to parse (e.g., 'tbk_kira.txt'). Defaults to all.",
    )

    args = parser.parse_args()

    logger.info("Starting Turkish law parsing pipeline...")
    results = parse_and_export_all(
        raw_dir=args.raw_dir,
        out_dir=args.out_dir,
        target_file=args.file,
    )

    total_articles = sum(len(arts) for arts in results.values())
    logger.info(
        f"Law parsing completed: {len(results)} files processed, {total_articles} total articles generated."
    )


if __name__ == "__main__":
    main()
