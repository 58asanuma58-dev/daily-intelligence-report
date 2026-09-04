"""複数の記事と前回比較から、簡単なシグナルを作る。"""

from typing import Any


def generate_signals(
    articles: list[dict[str, Any]],
    changes: list[dict[str, str]],
    settings: dict[str, Any],
) -> list[dict[str, str]]:
    """理解しやすい4種類のルールでシグナルを作る。"""
    signals: list[dict[str, str]] = []

    for change in changes:
        if change.get("type") in {"TREND UP", "NEW TOPIC"}:
            signals.append(
                {
                    "label": str(change["type"]),
                    "title": str(change.get("theme", "")),
                    "detail": str(change.get("change", "")),
                }
            )

    for article in articles:
        if int(article.get("duplicate_count", 1)) >= 2:
            signals.append(
                {
                    "label": "MULTIPLE SOURCES",
                    "title": str(article.get("title", "")),
                    "detail": f"{article['duplicate_count']}件・{len(article.get('duplicate_sources', []))}情報源の関連記事があります。",
                }
            )

        if int(article.get("importance_score", 0)) >= int(
            settings.get("high_priority_threshold", 8)
        ):
            signals.append(
                {
                    "label": "HIGH PRIORITY",
                    "title": str(article.get("title", "")),
                    "detail": f"重要度 {article['importance_score']}/10 です。",
                }
            )

    unique_signals: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for signal in signals:
        key = (signal["label"], signal["title"])
        if key not in seen:
            seen.add(key)
            unique_signals.append(signal)

    return unique_signals[: int(settings.get("max_signals", 10))]
