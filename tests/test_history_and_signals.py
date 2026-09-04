import json

from comparator import compare_with_previous
from signals import generate_signals
from storage import load_previous_history, save_json


def test_history_skips_broken_newest_file(tmp_path):
    save_json(tmp_path / "2026-09-01.json", {"articles": [{"id": "1"}]})
    (tmp_path / "2026-09-02.json").write_text("broken", encoding="utf-8")
    history = load_previous_history(tmp_path, "2026-09-03")
    assert history["articles"][0]["id"] == "1"


def test_comparison_and_signals_detect_changes():
    previous = {"articles": [{"id": "old", "keywords": ["rates"], "importance_score": 3}]}
    current = [{
        "id": "new", "title": "Rate decision", "source": "A", "keywords": ["rates"],
        "importance_score": 9, "relevance_score": 3, "duplicate_count": 2,
        "duplicate_sources": ["A", "B"], "watchlist_topics": [], "category": "Economy",
    }]
    changes = compare_with_previous(current, previous, {"max_changes": 10})
    assert any(change["type"] == "IMPORTANCE UP" for change in changes)
    assert any(change["type"] == "NEW ARTICLE" for change in changes)
    signals = generate_signals(current, changes, {"high_priority_threshold": 8, "max_signals": 10})
    labels = {signal["label"] for signal in signals}
    assert {"MULTIPLE SOURCES", "HIGH PRIORITY"} <= labels
