"""前回履歴と今日の記事を比較し、「何が変わったか」を作る。"""

from collections import defaultdict
from typing import Any


def article_themes(article: dict[str, Any]) -> set[str]:
    """Watch List、分類キーワード、カテゴリから記事のテーマを作る。"""
    themes = {
        str(theme) for theme in article.get("watchlist_topics", []) if str(theme)
    }
    themes.update(str(keyword) for keyword in article.get("keywords", []) if str(keyword))
    if not themes and article.get("category"):
        themes.add(str(article["category"]))
    return themes


def _theme_stats(articles: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    stats: defaultdict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "max_importance": 0}
    )
    for article in articles:
        for theme in article_themes(article):
            stats[theme]["count"] += 1
            stats[theme]["max_importance"] = max(
                stats[theme]["max_importance"],
                int(article.get("importance_score", 0)),
            )
    return dict(stats)


def compare_with_previous(
    current_articles: list[dict[str, Any]],
    previous_history: dict[str, Any] | None,
    settings: dict[str, Any],
) -> list[dict[str, str]]:
    """新規テーマ、記事数増加、重要度上昇、新着記事を検出する。"""
    maximum = int(settings.get("max_changes", 10))
    current_stats = _theme_stats(current_articles)

    if not previous_history:
        return [
            {
                "type": "BASELINE",
                "theme": "初回記録",
                "yesterday": "比較できる履歴なし",
                "today": f"{len(current_articles)}件",
                "change": "本日を今後の比較基準として保存しました。",
            }
        ]

    previous_articles = previous_history.get("articles", [])
    previous_stats = _theme_stats(previous_articles)
    changes: list[dict[str, str]] = []

    for theme, today in current_stats.items():
        yesterday = previous_stats.get(theme)
        if yesterday is None:
            changes.append(
                {
                    "type": "NEW TOPIC",
                    "theme": theme,
                    "yesterday": "0件",
                    "today": f"{today['count']}件",
                    "change": "前回履歴になかったテーマです。",
                }
            )
            continue

        increase = today["count"] - yesterday["count"]
        ratio = today["count"] / max(1, yesterday["count"])
        if increase >= int(settings.get("trend_minimum_increase", 2)) and ratio >= float(
            settings.get("trend_ratio", 1.5)
        ):
            changes.append(
                {
                    "type": "TREND UP",
                    "theme": theme,
                    "yesterday": f"{yesterday['count']}件",
                    "today": f"{today['count']}件",
                    "change": "同一テーマの記事数が増加しました。",
                }
            )

        if today["max_importance"] > yesterday["max_importance"]:
            changes.append(
                {
                    "type": "IMPORTANCE UP",
                    "theme": theme,
                    "yesterday": f"重要度 {yesterday['max_importance']}",
                    "today": f"重要度 {today['max_importance']}",
                    "change": "テーマ内の最高重要度が上昇しました。",
                }
            )

    previous_ids = {str(article.get("id")) for article in previous_articles}
    new_articles = sorted(
        (
            article
            for article in current_articles
            if str(article.get("id")) not in previous_ids
        ),
        key=lambda article: (
            int(article.get("importance_score", 0)),
            int(article.get("relevance_score", 0)),
        ),
        reverse=True,
    )
    for article in new_articles:
        changes.append(
            {
                "type": "NEW ARTICLE",
                "theme": str(article.get("title", "新着記事")),
                "yesterday": "掲載なし",
                "today": str(article.get("source", "")),
                "change": "前回履歴にない記事です。",
            }
        )

    return changes[:maximum]
