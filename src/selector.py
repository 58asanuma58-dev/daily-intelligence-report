"""採点済みニュースから、今日読む記事を選ぶ。"""

from collections import defaultdict
from typing import Any


def _sort_key(article: dict[str, Any]) -> tuple[int, int, str]:
    return (
        int(article.get("importance_score", 0)),
        int(article.get("relevance_score", 0)),
        str(article.get("published_at", "")),
    )


def select_top_articles(
    articles: list[dict[str, Any]], count: int
) -> list[dict[str, Any]]:
    """重要度、関連度、公開日時の順に上位記事を選ぶ。"""
    return sorted(articles, key=_sort_key, reverse=True)[:count]


def select_category_digest(
    articles: list[dict[str, Any]], maximum_per_category: int
) -> dict[str, list[dict[str, Any]]]:
    """カテゴリごとに上位記事を選ぶ。"""
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for article in sorted(articles, key=_sort_key, reverse=True):
        category = str(article.get("category", "Other Important Developments"))
        if len(grouped[category]) < maximum_per_category:
            grouped[category].append(article)
    return dict(grouped)
