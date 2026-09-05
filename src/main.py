"""Daily Intelligence Report Version 1の全処理を順番に実行する。"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

from classifier import classify_articles, filter_articles_by_period
from comparator import compare_with_previous
from content_enricher import enrich_articles
from deduplicator import group_duplicate_articles
from fetcher import fetch_all_sources
from normalizer import normalize_articles
from pdf_generator import generate_pdf
from report_generator import build_takeaways, generate_html
from scoring import score_articles
from selector import select_category_digest, select_top_articles
from signals import generate_signals
from storage import load_previous_history, load_summary_cache, previous_keywords, save_json
from summarizer import summarize_articles
from utils import load_yaml, setup_logging


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMPLATE_DIR = PROJECT_ROOT / "templates"
LOG_DIR = PROJECT_ROOT / "logs"
JST = ZoneInfo("Asia/Tokyo")


def _validate_config(configs: dict[str, dict[str, Any]]) -> None:
    """実行に不可欠な設定項目だけを、分かりやすいエラーで確認する。"""
    if not isinstance(configs["sources"].get("sources"), list):
        raise ValueError("sources.yaml に sources の一覧がありません。")
    if not isinstance(configs["categories"].get("categories"), list):
        raise ValueError("categories.yaml に categories の一覧がありません。")
    if not isinstance(configs["watchlist"].get("topics"), list):
        raise ValueError("watchlist.yaml に topics の一覧がありません。")


def load_all_configs() -> dict[str, dict[str, Any]]:
    """Version 1で使う5つのYAML設定をまとめて読み込む。"""
    configs = {
        "sources": load_yaml(CONFIG_DIR / "sources.yaml"),
        "categories": load_yaml(CONFIG_DIR / "categories.yaml"),
        "interests": load_yaml(CONFIG_DIR / "interests.yaml"),
        "watchlist": load_yaml(CONFIG_DIR / "watchlist.yaml"),
        "settings": load_yaml(CONFIG_DIR / "settings.yaml"),
    }
    _validate_config(configs)
    return configs


def source_reliability(config: dict[str, Any]) -> dict[str, int]:
    """情報源名から信頼性点を引ける辞書を作る。"""
    return {
        str(source.get("name")): int(source.get("reliability", 0))
        for source in config.get("sources", [])
    }


def build_report_context(
    report_date: str,
    generated_at: str,
    lookback_hours: int,
    articles: list[dict[str, Any]],
    top_articles: list[dict[str, Any]],
    category_digest: dict[str, list[dict[str, Any]]],
    changes: list[dict[str, str]],
    report_signals: list[dict[str, str]],
    fetch_errors: list[str],
    source_success: int,
    selection_settings: dict[str, Any],
) -> dict[str, Any]:
    """HTMLテンプレートで使う値を1つの辞書へまとめる。"""
    return {
        "report_date": report_date,
        "generated_at": generated_at,
        "target_period": f"過去 {lookback_hours}時間",
        "stats": {
            "source_success": source_success,
            "article_count": len(articles),
        },
        "executive_summary": top_articles[
            : int(selection_settings.get("executive_max", 5))
        ],
        "top_articles": top_articles,
        "changes": changes,
        "category_digest": category_digest,
        "watchlist_articles": [article for article in articles if article.get("is_watchlist")],
        "signals": report_signals,
        "takeaways": build_takeaways(
            top_articles, int(selection_settings.get("takeaway_max", 5))
        ),
        "fetch_errors": fetch_errors,
    }


def run() -> dict[str, Path]:
    """取得からPDF生成までを実行し、作成したファイルを返す。"""
    now_utc = datetime.now(timezone.utc)
    now_jst = now_utc.astimezone(JST)
    report_date = now_jst.date().isoformat()
    logger = setup_logging(LOG_DIR / f"{report_date}.log")
    logger.info("START Daily Intelligence Report")

    configs = load_all_configs()
    sources_config = configs["sources"]
    category_config = configs["categories"]
    settings = configs["settings"]
    selection_settings = settings.get("selection", {})
    reliability = source_reliability(sources_config)

    max_items = int(sources_config.get("max_items_per_source", 20))
    raw_articles, fetch_errors = fetch_all_sources(
        sources_config["sources"], max_items
    )
    raw_path = DATA_DIR / "raw" / f"{report_date}.json"
    save_json(raw_path, raw_articles)
    logger.info("RAW SAVED %s (%d articles)", raw_path, len(raw_articles))
    if not raw_articles:
        raise RuntimeError("すべてのRSS取得に失敗し、記事を1件も取得できませんでした。")

    normalized = normalize_articles(raw_articles)
    lookback_hours = int(category_config.get("lookback_hours", 48))
    recent, excluded = filter_articles_by_period(normalized, lookback_hours, now_utc)
    classified = classify_articles(recent, category_config)
    grouped = group_duplicate_articles(
        classified, settings.get("deduplication", {}), reliability
    )
    logger.info(
        "PROCESSED recent=%d excluded=%d grouped=%d duplicates_merged=%d",
        len(recent),
        len(excluded),
        len(grouped),
        len(recent) - len(grouped),
    )

    summarization_settings = settings.get("summarization", {})
    enriched = enrich_articles(
        grouped, int(summarization_settings.get("source_text_maximum_chars", 3500))
    )
    summary_cache = load_summary_cache(DATA_DIR / "history")
    summarized = summarize_articles(enriched, settings, cached_summaries=summary_cache)
    previous_history = load_previous_history(DATA_DIR / "history", report_date)
    scored = score_articles(
        summarized,
        reliability,
        configs["interests"],
        configs["watchlist"],
        settings,
        previous_keywords(previous_history),
        now_utc,
    )
    top_articles = select_top_articles(
        scored, int(selection_settings.get("top_count", 10))
    )
    category_digest = select_category_digest(
        scored, int(selection_settings.get("category_max", 5))
    )
    changes = compare_with_previous(
        scored, previous_history, settings.get("comparison", {})
    )
    report_signals = generate_signals(
        scored, changes, settings.get("signals", {})
    )

    source_success = sum(
        1 for source in sources_config["sources"] if source.get("enabled", True)
    ) - len(fetch_errors)
    generated_at = now_jst.isoformat(timespec="seconds")
    processed_data = {
        "report_date": report_date,
        "generated_at": generated_at,
        "target_period_hours": lookback_hours,
        "stats": {
            "raw_articles": len(raw_articles),
            "period_excluded": len(excluded),
            "articles_before_grouping": len(recent),
            "story_groups": len(scored),
            "duplicates_merged": len(recent) - len(grouped),
            "source_success": source_success,
            "source_failures": len(fetch_errors),
        },
        "fetch_errors": fetch_errors,
        "articles": scored,
        "changes": changes,
        "signals": report_signals,
    }
    processed_path = DATA_DIR / "processed" / f"{report_date}.json"
    history_path = DATA_DIR / "history" / f"{report_date}.json"
    save_json(processed_path, processed_data)

    context = build_report_context(
        report_date,
        generated_at,
        lookback_hours,
        scored,
        top_articles,
        category_digest,
        changes,
        report_signals,
        fetch_errors,
        source_success,
        selection_settings,
    )
    html_path = OUTPUT_DIR / "html" / f"daily-intelligence-{report_date}.html"
    pdf_path = OUTPUT_DIR / "pdf" / f"daily-intelligence-{report_date}.pdf"
    generate_html(context, TEMPLATE_DIR, html_path)
    logger.info("HTML GENERATED %s", html_path)
    generate_pdf(html_path, pdf_path)
    logger.info("PDF GENERATED %s", pdf_path)
    # 完成したレポートだけを翌日の比較対象にする。
    # PDF生成に失敗した日の途中データが基準になることを防ぐため、最後に保存する。
    save_json(history_path, processed_data)
    logger.info("HISTORY SAVED %s", history_path)
    logger.info("COMPLETE")
    return {
        "raw": raw_path,
        "processed": processed_path,
        "history": history_path,
        "html": html_path,
        "pdf": pdf_path,
        "log": LOG_DIR / f"{report_date}.log",
    }


def main() -> None:
    """失敗理由をログとターミナルへ残し、終了コードを返す。"""
    try:
        outputs = run()
    except Exception:
        logging.getLogger(__name__).exception("REPORT FAILED")
        raise SystemExit(1)

    print("\nDaily Intelligence Reportを生成しました:")
    for name, path in outputs.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
