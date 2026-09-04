from pathlib import Path

from report_generator import generate_html, why_it_matters


def test_html_report_escapes_article_content(tmp_path):
    project_root = Path(__file__).resolve().parent.parent
    article = {
        "title": "<script>alert(1)</script>", "category": "Science", "importance_score": 8,
        "relevance_score": 2, "summary": "Summary", "is_watchlist": False,
        "duplicate_count": 1, "source": "NASA", "published_at": "2026-09-03T00:00:00Z",
        "url": "https://example.com", "watchlist_topics": [], "score_details": {},
        "matched_interest_keywords": {},
    }
    context = {
        "report_date": "2026-09-04", "generated_at": "2026-09-04T06:30:00+09:00",
        "target_period": "過去 48時間", "stats": {"source_success": 1, "article_count": 1},
        "executive_summary": [article], "top_articles": [article], "changes": [],
        "category_digest": {"Science": [article]}, "watchlist_articles": [],
        "signals": [], "takeaways": ["Takeaway"], "fetch_errors": [],
    }
    output = tmp_path / "report.html"
    generate_html(context, project_root / "templates", output)
    html = output.read_text(encoding="utf-8")
    assert "&lt;script&gt;" in html
    assert "<script>alert(1)</script>" not in html
    assert "DAILY INTELLIGENCE" in html


def test_why_it_matters_uses_rule_reasons():
    article = {
        "category": "Medicine", "watchlist_topics": ["Clinical Research"],
        "duplicate_count": 2, "score_details": {"recent_24h": 2},
        "matched_interest_keywords": {"high_priority": ["clinical trial"]},
    }
    text = why_it_matters(article)
    assert "Watch List" in text and "2件" in text and "24時間以内" in text
