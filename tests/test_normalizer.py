from normalizer import normalize_article, normalize_published_at, normalize_text


def test_normalize_article_creates_common_format():
    raw = {
        "title": "  Example   News  ",
        "source": "Test Source",
        "published_at": "Thu, 03 Sep 2026 14:40:00 +0900",
        "url": "https://example.com/news/1",
        "summary": "<p>First <strong>summary</strong>.</p>",
    }
    article = normalize_article(raw)
    assert len(article) == 12
    assert article["title"] == "Example News"
    assert article["published_at"] == "2026-09-03T05:40:00Z"
    assert article["summary"] == "First summary."


def test_id_is_stable_when_same_url_has_new_title():
    base = {"source": "Example", "published_at": "", "summary": ""}
    first = normalize_article({**base, "title": "First", "url": "https://example.com/1"})
    second = normalize_article({**base, "title": "Changed", "url": "https://example.com/1"})
    assert first["id"] == second["id"]


def test_invalid_date_is_not_guessed():
    assert normalize_published_at("not-a-date") == ""
    assert normalize_text("  AI   news\n today  ") == "AI news today"
