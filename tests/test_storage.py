import json

from storage import load_summary_cache


def test_summary_cache_reuses_only_copilot_summaries(tmp_path):
    history = tmp_path / "history"
    history.mkdir()
    (history / "2026-09-05.json").write_text(
        json.dumps(
            {
                "articles": [
                    {"id": "good", "summary": "十分な日本語要約です。", "summary_method": "copilot"},
                    {"id": "fallback", "summary": "代替文です。", "summary_method": "fallback"},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assert load_summary_cache(history) == {"good": "十分な日本語要約です。"}
