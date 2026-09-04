from pathlib import Path
import shutil

from pypdf import PdfReader

from pdf_generator import generate_pdf


def test_pdf_is_a4_contains_japanese_and_page_number(tmp_path):
    """PDFの存在だけでなく、用紙・日本語・フッターも検証する。"""
    source_root = Path(__file__).resolve().parent.parent
    project = tmp_path / "project"
    html_path = project / "output" / "html" / "test.html"
    pdf_path = project / "output" / "pdf" / "test.pdf"
    font_dir = project / "assets" / "fonts"
    template_dir = project / "templates"
    font_dir.mkdir(parents=True)
    template_dir.mkdir(parents=True)
    html_path.parent.mkdir(parents=True)
    shutil.copy2(
        source_root / "assets" / "fonts" / "NotoSansJP-Regular.ttf",
        font_dir / "NotoSansJP-Regular.ttf",
    )
    shutil.copy2(
        source_root / "templates" / "pdf_style.css",
        template_dir / "pdf_style.css",
    )
    html_path.write_text(
        "<!doctype html><html><head><style>body{}</style></head>"
        "<body><main><h1>日本語テスト</h1><p>重要なニュース</p>"
        "</main></body></html>",
        encoding="utf-8",
    )

    generate_pdf(html_path, pdf_path)

    reader = PdfReader(pdf_path)
    assert len(reader.pages) == 1
    page = reader.pages[0]
    assert abs(float(page.mediabox.width) - 595.28) < 1
    assert abs(float(page.mediabox.height) - 841.89) < 1
    text = page.extract_text()
    assert "日本語テスト" in text
    assert "Page 1 / 1" in text
