from datetime import datetime, timezone

from scoring import score_articles


SETTINGS = {
    "scoring": {
        "reliable_source": 3, "watchlist": 3, "multiple_sources": 2,
        "recent_24h": 2, "important_keyword": 2, "new_topic": 2,
        "many_duplicates_penalty": -1, "high_reliability_minimum": 4,
        "many_duplicates_minimum": 4,
    },
    "relevance": {"high_priority": 3, "medium_priority": 2, "low_priority": 1},
}


def test_scores_are_bounded_and_explainable():
    article = {
        "title": "New generative AI product",
        "summary": "",
        "source": "OpenAI",
        "published_at": "2026-09-03T12:00:00Z",
        "keywords": ["generative ai"],
        "duplicate_count": 2,
        "duplicate_sources": ["OpenAI", "Google AI"],
    }
    scored = score_articles(
        [article], {"OpenAI": 5}, {"high_priority": ["generative ai"]},
        {"topics": [{"name": "AI Products", "keywords": ["generative ai"]}]},
        SETTINGS, {"old topic"}, datetime(2026, 9, 4, tzinfo=timezone.utc),
    )[0]
    assert scored["importance_score"] == 10
    assert scored["relevance_score"] == 3
    assert scored["is_watchlist"] is True
    assert "reliable_source" in scored["score_details"]
    assert "new_topic" in scored["score_details"]
