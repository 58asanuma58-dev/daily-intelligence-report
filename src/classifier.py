"""対象期間の記事を選び、設定されたキーワードで分類する。"""

from datetime import datetime, timedelta, timezone
import re
from typing import Any

from normalizer import normalize_text


def parse_iso_datetime(value: Any) -> datetime | None:
    """標準化済みのISO日時をdatetimeへ戻す。読めない場合はNoneを返す。"""
    text = normalize_text(value)
    if not text:
        return None

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def filter_articles_by_period(
    articles: list[dict[str, Any]],
    lookback_hours: int,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """指定時間内の記事と、対象外の記事に分ける。"""
    if lookback_hours <= 0:
        raise ValueError("lookback_hours は1以上にしてください。")

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    current_time = current_time.astimezone(timezone.utc)
    oldest_time = current_time - timedelta(hours=lookback_hours)

    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    for article in articles:
        published_at = parse_iso_datetime(article.get("published_at"))
        if published_at is not None and oldest_time <= published_at <= current_time:
            included.append(article)
        else:
            excluded.append(article)

    return included, excluded


def contains_keyword(text: str, keyword: str) -> bool:
    """英数字は単語単位、日本語は部分一致でキーワードを探す。"""
    keyword_lower = normalize_text(keyword).lower()
    if not keyword_lower:
        return False

    if keyword_lower.isascii():
        pattern = rf"(?<!\w){re.escape(keyword_lower)}(?!\w)"
        return re.search(pattern, text) is not None

    return keyword_lower in text


def classify_article(
    article: dict[str, Any], category_config: dict[str, Any]
) -> dict[str, Any]:
    """ニュース1件のカテゴリと一致キーワードを決める。"""
    searchable_text = " ".join(
        [
            normalize_text(article.get("title")),
            normalize_text(article.get("summary")),
        ]
    ).lower()

    best_category = ""
    best_keywords: list[str] = []

    for category in category_config.get("categories", []):
        matched_keywords = [
            keyword
            for keyword in category.get("keywords", [])
            if contains_keyword(searchable_text, str(keyword))
        ]
        if len(matched_keywords) > len(best_keywords):
            best_category = normalize_text(category.get("name"))
            best_keywords = matched_keywords

    if not best_category:
        source_defaults = category_config.get("source_defaults", {})
        best_category = source_defaults.get(
            article.get("source"),
            category_config.get("default_category", "Other Important Developments"),
        )

    classified = dict(article)
    classified["category"] = best_category
    classified["keywords"] = best_keywords
    return classified


def classify_articles(
    articles: list[dict[str, Any]], category_config: dict[str, Any]
) -> list[dict[str, Any]]:
    """ニュース一覧を1件ずつ分類する。"""
    return [classify_article(article, category_config) for article in articles]
