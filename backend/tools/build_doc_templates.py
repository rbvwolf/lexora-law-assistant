"""Build the .docx document templates in settings.TEMPLATES_DIR with python-docx.

Why generate instead of editing in Word: docxtpl only replaces a {{ tag }} that sits inside a
single run, and Word splits runs on spell-check / revision marks. Here every tag is written by
one add_run() call, so it stays intact. tests/test_doc_service.py fails if a tag is ever split.

Text and layout come from app/services/doc_layouts.py, the same source the PDF renderer uses.

Usage (from backend/):
    python -m tools.build_doc_templates
"""

import argparse
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from app.core.config import settings
from app.services.doc_layouts import (
    FIRST_LINE_INDENT_CM,
    FONT_SIZE_PT,
    FOOTER_FONT_SIZE_PT,
    PAGE_MARGIN_CM,
    SPACE_AFTER_PT,
    DocumentLayout,
    get_layout,
    layout_template_ids,
)

FONT_NAME = "Times New Roman"

_ALIGN = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def build_docx(layout: DocumentLayout, out_path: Path) -> Path:
    doc = Document()
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    for side in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(section, side, Cm(PAGE_MARGIN_CM))

    normal = doc.styles["Normal"]
    normal.font.name = FONT_NAME
    normal.font.size = Pt(FONT_SIZE_PT)
    # East Asian slot too, so Word never falls back to another font for any glyph
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT_NAME)
    normal.paragraph_format.space_after = Pt(SPACE_AFTER_PT)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run(layout.footer)
    run.font.size = Pt(FOOTER_FONT_SIZE_PT)
    run.italic = True

    for spec in layout.paragraphs:
        paragraph = doc.add_paragraph()
        paragraph.alignment = _ALIGN[spec.align]
        if spec.first_line_indent:
            paragraph.paragraph_format.first_line_indent = Cm(FIRST_LINE_INDENT_CM)
        for text, bold in spec.segments:
            paragraph.add_run(text).bold = bold

    doc.save(str(out_path))
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", default=settings.TEMPLATES_DIR, help="Output directory (default: TEMPLATES_DIR)")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for template_id in layout_template_ids():
        print(f"Wrote {build_docx(get_layout(template_id), out_dir / f'{template_id}.docx')}")


if __name__ == "__main__":
    main()
