"""完成したHTML/CSSをA4 PDFへ変換し、ページ番号を追加する。"""

from io import BytesIO
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.parse import unquote, urlparse

from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from xhtml2pdf import pisa


PDF_FONT = "ReportJP"


def _register_pdf_font(html_path: Path) -> None:
    """オープンライセンスの日本語フォントをPDFへ埋め込めるよう登録する。"""
    font_path = html_path.parents[2] / "assets" / "fonts" / "NotoSansJP-Regular.ttf"
    if not font_path.exists():
        raise RuntimeError(f"日本語フォントが見つかりません: {font_path}")
    if PDF_FONT not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(PDF_FONT, str(font_path)))


def _pdf_html(html_path: Path) -> str:
    """画面用CSSを、PDF変換器と互換性のあるCSSへ差し替える。"""
    html = html_path.read_text(encoding="utf-8")
    project_root = html_path.parents[2]
    pdf_css = (project_root / "templates" / "pdf_style.css").read_text(
        encoding="utf-8"
    )
    font_path = project_root / "assets" / "fonts" / "NotoSansJP-Regular.ttf"
    font_face = (
        f"@font-face {{ font-family: {PDF_FONT}; "
        f"src: url('{font_path.resolve().as_uri()}'); }}\n"
    )
    return re.sub(
        r"<style>.*?</style>",
        f"<style>{font_face}{pdf_css}</style>",
        html,
        count=1,
        flags=re.DOTALL,
    )


def _add_page_numbers(raw_pdf: Path, final_pdf: Path) -> None:
    """各ページの下部へレポート名とページ番号を重ねる。"""
    reader = PdfReader(raw_pdf)
    writer = PdfWriter()
    total_pages = len(reader.pages)

    for number, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        overlay_stream = BytesIO()
        overlay = canvas.Canvas(overlay_stream, pagesize=(width, height))
        overlay.setFont(PDF_FONT, 7)
        overlay.setFillColorRGB(0.38, 0.45, 0.54)
        overlay.drawString(42, 20, "DAILY INTELLIGENCE REPORT")
        overlay.drawRightString(width - 42, 20, f"Page {number} / {total_pages}")
        overlay.save()
        overlay_stream.seek(0)
        # 先にWriterへ追加してから重ねると、pypdf 7でも安全な操作になる。
        writer.add_page(page)
        writer.pages[-1].merge_page(PdfReader(overlay_stream).pages[0])

    with final_pdf.open("wb") as output:
        writer.write(output)


def _resolve_resource(uri: str, relative_to: str) -> str:
    """xhtml2pdfへfile URLの実ファイルパスを伝える。"""
    if uri.startswith("file:"):
        return unquote(urlparse(uri).path)
    path = Path(uri)
    if path.is_absolute():
        return str(path)
    return str((Path(relative_to).parent / path).resolve())


def generate_pdf(html_path: Path, pdf_path: Path) -> None:
    """HTMLをPDF化し、正常性を確認してページ番号を追加する。"""
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    _register_pdf_font(html_path)

    with NamedTemporaryFile(
        "wb", suffix=".pdf", dir=pdf_path.parent, delete=False
    ) as temporary_file:
        raw_pdf = Path(temporary_file.name)
        status = pisa.CreatePDF(
            _pdf_html(html_path),
            dest=temporary_file,
            encoding="utf-8",
            path=str(html_path.resolve()),
            link_callback=_resolve_resource,
        )

    try:
        if status.err or not raw_pdf.exists() or raw_pdf.stat().st_size == 0:
            raise RuntimeError(f"HTMLからPDFへの変換で{status.err}件のエラーが発生しました。")
        _add_page_numbers(raw_pdf, pdf_path)
    finally:
        raw_pdf.unlink(missing_ok=True)

    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError("PDFファイルが作成されませんでした。")
