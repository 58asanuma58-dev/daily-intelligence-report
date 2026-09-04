"""情報源ごとの差をそろえ、すべての記事を同じ形式にする。"""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from html.parser import HTMLParser
from typing import Any


class _HTMLTextExtractor(HTMLParser):
    """HTMLタグを除き、画面に表示される文字だけを集める。"""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"br", "div", "li", "p"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"div", "li", "p"}:
            self.parts.append(" ")

    def text(self) -> str:
        # 文字片をそのまま連結すると、句点の前に不要な空白が入りません。
        return normalize_text("".join(self.parts))


def normalize_text(value: Any) -> str:
    """値を文字列にし、改行や連続する空白を1個へそろえる。"""
    if value is None:
        return ""
    return " ".join(str(value).split())


def remove_html(value: Any) -> str:
    """RSS概要に含まれるHTMLタグを除去する。"""
    parser = _HTMLTextExtractor()
    parser.feed(str(value or ""))
    return parser.text()


def normalize_published_at(value: Any) -> str:
    """さまざまな日時表記をUTCのISO 8601形式へ統一する。"""
    text = normalize_text(value)
    if not text:
        return ""

    try:
        published_at = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        try:
            published_at = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            # 読めない日時を推測で補わず、空欄にして異常が分かるようにします。
            return ""

    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    return published_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def create_article_id(article: dict[str, Any]) -> str:
    """同じ記事からは毎回同じIDが作られるようにする。"""
    url = normalize_text(article.get("url"))
    if url:
        identity_text = url
    else:
        identity_text = "|".join(
            [
                normalize_text(article.get("title")),
                normalize_text(article.get("source")),
            ]
        )
    return sha256(identity_text.encode("utf-8")).hexdigest()[:16]


def normalize_article(article: dict[str, Any]) -> dict[str, Any]:
    """ニュース1件をプロジェクト共通の12項目へ変換する。"""
    normalized = {
        "id": "",
        "title": normalize_text(article.get("title")) or "タイトルなし",
        "source": normalize_text(article.get("source")) or "情報源不明",
        "published_at": normalize_published_at(article.get("published_at")),
        "url": normalize_text(article.get("url")),
        "summary": remove_html(article.get("summary")),
        # 以下は後のPhaseで値を計算します。今は初期値だけ用意します。
        "category": "",
        "importance_score": 0,
        "relevance_score": 0,
        "keywords": [],
        "duplicate_group": "",
        "is_watchlist": False,
    }
    normalized["id"] = create_article_id(normalized)
    return normalized


def normalize_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """ニュース一覧を、1件ずつ共通形式へ変換する。"""
    return [normalize_article(article) for article in articles]
