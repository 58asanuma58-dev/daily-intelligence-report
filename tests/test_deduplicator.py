from deduplicator import group_duplicate_articles


def article(identifier, title, source):
    return {
        "id": identifier,
        "title": title,
        "source": source,
        "summary": "summary",
        "category": "Economy",
        "published_at": "2026-09-03T00:00:00Z",
        "url": f"https://example.com/{identifier}",
    }


def test_similar_titles_become_one_story_group():
    articles = [
        article("1", "Central bank raises interest rates", "A"),
        article("2", "Central bank raises the interest rate", "B"),
        article("3", "Employment report is released", "A"),
    ]
    groups = group_duplicate_articles(
        articles,
        {"title_similarity": 0.70, "token_overlap": 0.50, "max_hours_apart": 48},
        {"A": 4, "B": 5},
    )
    assert len(groups) == 2
    merged = next(group for group in groups if group["duplicate_count"] == 2)
    assert merged["source"] == "B"
    assert merged["duplicate_sources"] == ["A", "B"]
    assert len(merged["related_articles"]) == 2
