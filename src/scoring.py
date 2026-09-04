"""Watch List、重要度、自分との関連度をルールで計算する。"""

from datetime import datetime, timezone
from typing import Any

from classifier import contains_keyword, parse_iso_datetime
from normalizer import normalize_text


def _article_text(article: dict[str, Any]) -> str:
    return " ".join(
        [normalize_text(article.get("title")), normalize_text(article.get("summary"))]
    ).lower()


def matching_keywords(text: str, keywords: list[Any]) -> list[str]:
    """本文中に見つかったキーワードだけを返す。"""
    return [str(keyword) for keyword in keywords if contains_keyword(text, str(keyword))]


def apply_watchlist(
    article: dict[str, Any], watchlist_config: dict[str, Any]
) -> dict[str, Any]:
    """記事がどのWatch Listテーマに該当するかを記録する。"""
    text = _article_text(article)
    topics = [
        str(topic.get("name"))
        for topic in watchlist_config.get("topics", [])
        if matching_keywords(text, topic.get("keywords", []))
    ]
    updated = dict(article)
    updated["is_watchlist"] = bool(topics)
    updated["watchlist_topics"] = topics
    return updated


def _interest_matches(
    text: str, interests_config: dict[str, Any]
) -> dict[str, list[str]]:
    return {
        priority: matching_keywords(text, interests_config.get(priority, []))
        for priority in ("high_priority", "medium_priority", "low_priority")
    }


def score_article(
    article: dict[str, Any],
    reliability: int,
    interests_config: dict[str, Any],
    settings: dict[str, Any],
    previous_keywords: set[str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """ニュース1件へ重要度と関連度、その理由を追加する。"""
    weights = settings.get("scoring", {})
    relevance_weights = settings.get("relevance", {})
    current_time = now or datetime.now(timezone.utc)
    text = _article_text(article)
    interest_matches = _interest_matches(text, interests_config)
    details: dict[str, int] = {}

    if reliability >= int(weights.get("high_reliability_minimum", 4)):
        details["reliable_source"] = int(weights.get("reliable_source", 3))
    if article.get("is_watchlist"):
        details["watchlist"] = int(weights.get("watchlist", 3))
    if len(set(article.get("duplicate_sources", []))) >= 2:
        details["multiple_sources"] = int(weights.get("multiple_sources", 2))

    published_at = parse_iso_datetime(article.get("published_at"))
    if published_at is not None:
        age_hours = (current_time.astimezone(timezone.utc) - published_at).total_seconds() / 3600
        if 0 <= age_hours <= 24:
            details["recent_24h"] = int(weights.get("recent_24h", 2))

    if interest_matches["high_priority"]:
        details["important_keyword"] = int(weights.get("important_keyword", 2))

    known_keywords = previous_keywords or set()
    article_keywords = {str(keyword).lower() for keyword in article.get("keywords", [])}
    if known_keywords and article_keywords - known_keywords:
        details["new_topic"] = int(weights.get("new_topic", 2))

    if int(article.get("duplicate_count", 1)) >= int(
        weights.get("many_duplicates_minimum", 4)
    ):
        details["many_duplicates"] = int(weights.get("many_duplicates_penalty", -1))

    importance_score = max(0, min(10, sum(details.values())))

    relevance_details: dict[str, int] = {}
    for priority in ("high_priority", "medium_priority", "low_priority"):
        if interest_matches[priority]:
            relevance_details[priority] = int(relevance_weights.get(priority, 0))
    relevance_score = max(0, min(5, sum(relevance_details.values())))

    scored = dict(article)
    scored["importance_score"] = importance_score
    scored["relevance_score"] = relevance_score
    scored["score_details"] = details
    scored["relevance_details"] = relevance_details
    scored["matched_interest_keywords"] = interest_matches
    return scored


def score_articles(
    articles: list[dict[str, Any]],
    source_reliability: dict[str, int],
    interests_config: dict[str, Any],
    watchlist_config: dict[str, Any],
    settings: dict[str, Any],
    previous_keywords: set[str] | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Watch List判定後、ニュース一覧を1件ずつ採点する。"""
    return [
        score_article(
            apply_watchlist(article, watchlist_config),
            source_reliability.get(str(article.get("source")), 0),
            interests_config,
            settings,
            previous_keywords,
            now,
        )
        for article in articles
    ]
