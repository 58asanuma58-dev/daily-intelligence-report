"""処理済みデータから、読みやすいHTMLレポートを生成する。"""

from pathlib import Path
import re
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


def shorten(text: Any, maximum: int = 420) -> str:
    """意味を壊しにくい位置で長い文章を短くする。"""
    clean = " ".join(str(text or "").split())
    if len(clean) <= maximum:
        return clean
    shortened = clean[:maximum]
    sentence_end = max(shortened.rfind("。"), shortened.rfind(". "))
    if sentence_end >= maximum // 2:
        shortened = shortened[: sentence_end + 1]
    return shortened.rstrip() + "…"


def article_summary(article: dict[str, Any]) -> str:
    """生成済みの日本語要約を読みやすい長さにする。"""
    summary = shorten(article.get("summary"))
    return summary or "日本語要約を生成できませんでした。元記事で詳細を確認してください。"


def why_it_matters(article: dict[str, Any]) -> str:
    """採点理由を組み合わせ、機械的なWhy it mattersを作る。"""
    reasons: list[str] = []
    if article.get("watchlist_topics"):
        reasons.append("Watch Listの「" + "、".join(article["watchlist_topics"]) + "」に該当")
    if int(article.get("duplicate_count", 1)) >= 2:
        reasons.append(f"{article['duplicate_count']}件の関連記事を確認")
    if article.get("score_details", {}).get("recent_24h"):
        reasons.append("24時間以内に公開")
    if article.get("matched_interest_keywords", {}).get("high_priority"):
        reasons.append("高優先の関心キーワードに一致")
    if not reasons:
        reasons.append(f"{article.get('category', '重要分野')}の更新として記録")
    return "。".join(reasons) + "。"


def build_takeaways(
    top_articles: list[dict[str, Any]], maximum: int
) -> list[str]:
    """上位記事から「今日覚えておくこと」を機械的に作る。"""
    return [
        f"[{article.get('category')}] {shorten(article.get('summary'), 120)}（重要度 {article.get('importance_score')}/10）"
        for article in top_articles[:maximum]
    ]


def generate_html(
    context: dict[str, Any], template_dir: Path, output_path: Path
) -> None:
    """Jinja2テンプレートへデータを渡し、UTF-8のHTMLを保存する。"""
    environment = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["summary"] = article_summary
    environment.filters["why"] = why_it_matters
    environment.filters["display_time"] = lambda value: re.sub("T", " ", str(value)).replace("Z", " UTC")
    template = environment.get_template("report.html")
    css = (template_dir / "style.css").read_text(encoding="utf-8")
    html = template.render(**context, style_css=css)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
