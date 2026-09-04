"""RSSフィードを取得し、RSSに含まれる5項目を取り出す。"""

from typing import Any

import feedparser
import logging
import requests


LOGGER = logging.getLogger(__name__)


def _published_at(entry: Any) -> str:
    """RSSごとに異なる公開日時の項目名を吸収する。"""
    return entry.get("published") or entry.get("updated") or "不明"


def fetch_feed(source: dict[str, Any], max_items: int) -> list[dict[str, str]]:
    """1つのRSSを取得し、指定件数までニュース辞書へ変換する。"""
    # requestsは信頼済み証明書を同梱するため、OSごとのSSL差を減らせます。
    response = requests.get(
        source["url"],
        timeout=20,
        headers={"User-Agent": "PersonalDailyIntelligenceReport/1.0"},
    )
    response.raise_for_status()
    feed = feedparser.parse(response.content)

    # 壊れたRSSでも記事を読める場合があるため、記事が0件の時だけ失敗にします。
    if not feed.entries:
        reason = getattr(feed, "bozo_exception", "記事がありません")
        raise RuntimeError(f"RSSを読み込めませんでした: {reason}")

    articles: list[dict[str, str]] = []
    for entry in feed.entries[:max_items]:
        articles.append(
            {
                "title": entry.get("title", "タイトルなし").strip(),
                "source": source["name"],
                "published_at": _published_at(entry),
                "url": entry.get("link", "").strip(),
                "summary": entry.get("summary", ""),
            }
        )

    return articles


def fetch_all_sources(
    sources: list[dict[str, Any]], max_items: int
) -> tuple[list[dict[str, str]], list[str]]:
    """有効なRSSを順番に取得し、記事一覧とエラー一覧を返す。"""
    all_articles: list[dict[str, str]] = []
    errors: list[str] = []

    for source in sources:
        if not source.get("enabled", True):
            continue

        try:
            articles = fetch_feed(source, max_items)
            all_articles.extend(articles)
            LOGGER.info("SOURCE OK %s: %d articles", source["name"], len(articles))
        except Exception as error:
            message = f"[FAILED] {source.get('name', '名前なし')}: {error}"
            errors.append(message)
            LOGGER.error(message)

    return all_articles, errors
