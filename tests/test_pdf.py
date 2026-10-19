from pathlib import Path
import shutil

from PIL import Image
from pypdf import PdfReader
import pytest

from pdf_generator import generate_pdf


@pytest.fixture
def pdf_project(tmp_path):
    source_root = Path(__file__).resolve().parent.parent
    project = tmp_path / "日本語 project"
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
    return html_path, pdf_path


def test_pdf_is_a4_contains_japanese_and_page_number(pdf_project):
    """PDFの存在だけでなく、用紙・日本語・フッターも検証する。"""
    html_path, pdf_path = pdf_project
    generate_pdf(html_path, pdf_path)

    reader = PdfReader(pdf_path)
    assert len(reader.pages) == 1
    page = reader.pages[0]
    assert abs(float(page.mediabox.width) - 595.28) < 1
    assert abs(float(page.mediabox.height) - 841.89) < 1
    text = page.extract_text()
    assert "日本語テスト" in text
    assert "Page 1 / 1" in text


@pytest.mark.parametrize("resource_kind", ["absolute", "relative", "symlink"])
def test_pdf_blocks_resources_outside_html_and_fonts(pdf_project, caplog, resource_kind):
    """フォントを許可しても、ほかのディレクトリは読み込めない。"""
    html_path, pdf_path = pdf_project
    project = html_path.parents[2]
    outside_image = project / "private.png"
    Image.new("RGB", (1, 1), "red").save(outside_image)
    if resource_kind == "absolute":
        uri = outside_image.as_uri()
    elif resource_kind == "relative":
        uri = "../../private.png"
    else:
        linked_image = project / "assets" / "fonts" / "private.png"
        linked_image.symlink_to(outside_image)
        uri = linked_image.as_uri()
    html = html_path.read_text(encoding="utf-8")
    html_path.write_text(
        html.replace("</main>", f'<img src="{uri}"></main>'), encoding="utf-8"
    )

    generate_pdf(html_path, pdf_path)

    page = PdfReader(pdf_path).pages[0]
    assert not page.images
    assert "日本語テスト" in page.extract_text()
    assert any(
        "Blocked by the resource policy" in record.message
        and "private.png" in record.message
        for record in caplog.records
    )
