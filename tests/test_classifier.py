from datetime import datetime, timezone

from classifier import classify_article, contains_keyword, filter_articles_by_period


CONFIG = {
    "default_category": "Other",
    "source_defaults": {"NASA": "Science"},
    "categories": [
        {"name": "AI / Technology", "keywords": ["ai", "人工知能"]},
        {"name": "Economy", "keywords": ["金融政策", "economy"]},
    ],
}


def test_period_filter_uses_fixed_time():
    now = datetime(2026, 9, 4, tzinfo=timezone.utc)
    articles = [
        {"title": "recent", "published_at": "2026-09-02T01:00:00Z"},
        {"title": "old", "published_at": "2026-09-01T23:59:59Z"},
        {"title": "unknown", "published_at": ""},
    ]
    included, excluded = filter_articles_by_period(articles, 48, now)
    assert [article["title"] for article in included] == ["recent"]
    assert len(excluded) == 2


def test_short_english_keyword_uses_word_boundary():
    assert contains_keyword("new ai service", "ai")
    assert not contains_keyword("daily report", "ai")


def test_category_keyword_then_source_then_default():
    assert classify_article({"title": "人工知能", "summary": "", "source": "X"}, CONFIG)["category"] == "AI / Technology"
    assert classify_article({"title": "Moon", "summary": "", "source": "NASA"}, CONFIG)["category"] == "Science"
    assert classify_article({"title": "Other", "summary": "", "source": "X"}, CONFIG)["category"] == "Other"
