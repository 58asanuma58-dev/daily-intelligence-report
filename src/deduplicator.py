"""似た記事を検出し、情報を失わずニュースグループへまとめる。"""

from datetime import timedelta
from difflib import SequenceMatcher
from hashlib import sha256
import re
from typing import Any

from classifier import parse_iso_datetime
from normalizer import normalize_text


def normalized_title(value: Any) -> str:
    """比較しやすいよう、タイトルを小文字の単語列へ変換する。"""
    text = normalize_text(value).lower()
    return " ".join(re.findall(r"[a-z0-9]+|[ぁ-んァ-ヶ一-龠々]+", text))


def title_similarity(first: dict[str, Any], second: dict[str, Any]) -> float:
    """2つのタイトルがどの程度似ているかを0〜1で返す。"""
    first_title = normalized_title(first.get("title"))
    second_title = normalized_title(second.get("title"))
    if not first_title or not second_title:
        return 0.0
    return SequenceMatcher(None, first_title, second_title).ratio()


def token_overlap(first: dict[str, Any], second: dict[str, Any]) -> float:
    """2つのタイトルに共通する英単語の割合を返す。"""
    first_tokens = set(re.findall(r"[a-z0-9]+", normalized_title(first.get("title"))))
    second_tokens = set(re.findall(r"[a-z0-9]+", normalized_title(second.get("title"))))
    if not first_tokens or not second_tokens:
        return 0.0
    return len(first_tokens & second_tokens) / len(first_tokens | second_tokens)


def articles_are_similar(
    first: dict[str, Any], second: dict[str, Any], settings: dict[str, Any]
) -> bool:
    """カテゴリ、時刻、タイトルを使い、同じニュースか判定する。"""
    if first.get("category") != second.get("category"):
        return False

    first_time = parse_iso_datetime(first.get("published_at"))
    second_time = parse_iso_datetime(second.get("published_at"))
    if first_time is None or second_time is None:
        return False

    max_hours = float(settings.get("max_hours_apart", 48))
    if abs(first_time - second_time) > timedelta(hours=max_hours):
        return False

    return (
        title_similarity(first, second) >= float(settings.get("title_similarity", 0.76))
        or token_overlap(first, second) >= float(settings.get("token_overlap", 0.55))
    )


def _representative(
    group: list[dict[str, Any]], source_reliability: dict[str, int]
) -> dict[str, Any]:
    """信頼性と概要の充実度から、グループの代表記事を選ぶ。"""
    return max(
        group,
        key=lambda article: (
            source_reliability.get(str(article.get("source")), 0),
            len(str(article.get("summary", ""))),
            str(article.get("published_at", "")),
        ),
    )


def group_duplicate_articles(
    articles: list[dict[str, Any]],
    settings: dict[str, Any],
    source_reliability: dict[str, int],
) -> list[dict[str, Any]]:
    """類似記事をまとめ、代表記事へ関連情報を追加する。"""
    groups: list[list[dict[str, Any]]] = []

    for article in articles:
        matching_group = next(
            (
                group
                for group in groups
                if any(articles_are_similar(article, member, settings) for member in group)
            ),
            None,
        )
        if matching_group is None:
            groups.append([article])
        else:
            matching_group.append(article)

    grouped_articles: list[dict[str, Any]] = []
    for group in groups:
        representative = dict(_representative(group, source_reliability))
        member_ids = sorted(str(article.get("id")) for article in group)
        group_id = sha256("|".join(member_ids).encode("utf-8")).hexdigest()[:12]
        representative["duplicate_group"] = group_id
        representative["duplicate_count"] = len(group)
        representative["duplicate_sources"] = sorted(
            {str(article.get("source")) for article in group}
        )
        representative["related_articles"] = [
            {
                "title": article.get("title", ""),
                "source": article.get("source", ""),
                "published_at": article.get("published_at", ""),
                "url": article.get("url", ""),
            }
            for article in group
        ]
        grouped_articles.append(representative)

    return grouped_articles
