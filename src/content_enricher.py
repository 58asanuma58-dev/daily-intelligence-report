"""RSSだけでは不足する場合に、リンク先の本文を要約用の材料として補う。"""

from html.parser import HTMLParser
from io import BytesIO
import logging
import re
from typing import Any
from xml.etree import ElementTree

import requests
from pypdf import PdfReader


LOGGER = logging.getLogger(__name__)


class _ReadableHTMLParser(HTMLParser):
    """HTMLから説明文と本文らしい段落だけを取り出す軽量パーサー。"""

    def __init__(self) -> None:
        super().__init__()
        self.ignored_depth = 0
        self.capture_depth = 0
        self.parts: list[str] = []
        self.descriptions: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.lower(): value or "" for name, value in attrs}
        if tag in {"script", "style", "nav", "footer", "form", "svg", "noscript"}:
            self.ignored_depth += 1
        if tag in {"p", "h1", "h2", "h3", "li", "article", "main"}:
            self.capture_depth += 1
        if tag == "meta":
            key = (attributes.get("name") or attributes.get("property") or "").lower()
            if key in {"description", "og:description", "twitter:description"}:
                value = " ".join(attributes.get("content", "").split())
                if value:
                    self.descriptions.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "h1", "h2", "h3", "li", "article", "main"}:
            self.parts.append("\n")
            self.capture_depth = max(0, self.capture_depth - 1)
        if tag in {"script", "style", "nav", "footer", "form", "svg", "noscript"}:
            self.ignored_depth = max(0, self.ignored_depth - 1)

    def handle_data(self, data: str) -> None:
        if self.ignored_depth == 0 and self.capture_depth > 0:
            text = " ".join(data.split())
            if text:
                self.parts.append(text + " ")

    def text(self) -> str:
        values = self.descriptions + re.split(r"\n+", "".join(self.parts))
        unique: list[str] = []
        seen: set[str] = set()
        for value in values:
            clean = " ".join(value.split())
            if len(clean) >= 20 and clean not in seen:
                seen.add(clean)
                unique.append(clean)
        return "\n".join(unique)


def _xml_text(content: bytes) -> str:
    """気象庁などのXMLから、見出し・説明文を名前空間に依存せず抽出する。"""
    root = ElementTree.fromstring(content)
    values: list[str] = []
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        if local_name in {"Headline", "Text", "Title", "InfoKind"} and element.text:
            clean = " ".join(element.text.split())
            if len(clean) >= 8 and clean not in values:
                values.append(clean)
    return "\n".join(values)


def fetch_source_text(url: str, timeout: int = 20) -> str:
    """記事URLから要約材料を取得する。失敗は呼び出し側でRSS本文へフォールバックする。"""
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "PersonalDailyIntelligenceReport/2.0"},
    )
    response.raise_for_status()
    content_type = (response.headers.get("content-type") or "").lower()
    if "pdf" in content_type or response.content.startswith(b"%PDF"):
        reader = PdfReader(BytesIO(response.content))
        return "\n".join(page.extract_text() or "" for page in reader.pages[:8])
    prefix = response.content[:2000]
    # XHTMLページもapplication/xmlで返るため、気象庁XMLのReport要素を確認します。
    if b"<Report" in prefix and ("xml" in content_type or prefix.lstrip().startswith(b"<?xml")):
        return _xml_text(response.content)

    encoding = response.encoding
    if not encoding or encoding.lower() in {"iso-8859-1", "latin-1"}:
        encoding = response.apparent_encoding or "utf-8"
    html = response.content.decode(encoding, errors="replace")
    parser = _ReadableHTMLParser()
    parser.feed(html)
    return parser.text()


def enrich_articles(
    articles: list[dict[str, Any]], maximum_chars: int = 3500
) -> list[dict[str, Any]]:
    """全記事へRSS概要と公式ページ本文を合わせた一時的な要約材料を付ける。"""
    enriched: list[dict[str, Any]] = []
    for article in articles:
        item = dict(article)
        parts = [str(item.get("title", "")), str(item.get("summary", ""))]
        try:
            page_text = fetch_source_text(str(item.get("url", "")))
            if page_text:
                parts.append(page_text)
        except Exception as error:
            LOGGER.warning("CONTENT FALLBACK %s: %s", item.get("url", ""), error)
        item["_source_text"] = "\n".join(part for part in parts if part)[:maximum_chars]
        enriched.append(item)
    return enriched
