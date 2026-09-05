import json

import pytest

from summarizer import _clean_summary, _parse_response, summarize_articles


ARTICLE = {
    "id": "article-1",
    "title": "A new service",
    "source": "OpenAI",
    "summary": "An English RSS summary.",
    "_source_text": "The company launched a new service for hospitals on September 5.",
}


def test_copilot_summary_is_stored_and_source_text_is_removed(monkeypatch):
    monkeypatch.setenv("SUMMARY_PROVIDER", "copilot")
    response = json.dumps(
        {
            "summaries": {
                "article-1": "企業は9月5日、病院向けの新サービスを発表しました。対象となる医療機関の業務を支援する機能を提供する内容です。詳細な提供地域や価格は資料に記載されていません。"
            }
        },
        ensure_ascii=False,
    )
    result = summarize_articles(
        [ARTICLE], {"summarization": {"minimum_chars": 60}},
        runner=lambda prompt, timeout: response,
    )[0]
    assert result["summary"].startswith("企業は9月5日")
    assert result["summary_method"] == "copilot"
    assert "_source_text" not in result


def test_required_mode_rejects_missing_or_short_summary(monkeypatch):
    monkeypatch.setenv("SUMMARY_PROVIDER", "copilot")
    monkeypatch.setenv("SUMMARY_REQUIRED", "true")
    response = json.dumps({"summaries": {"article-1": "短すぎます。"}}, ensure_ascii=False)
    with pytest.raises(RuntimeError, match="品質条件"):
        summarize_articles(
            [ARTICLE], {"summarization": {"minimum_chars": 60}},
            runner=lambda prompt, timeout: response,
        )


def test_parser_accepts_unescaped_newline_from_cli():
    response = '{"summaries":{"article-1":"1文目です。\n2文目です。"}}'
    assert _parse_response(response)["article-1"] == "1文目です。 2文目です。"


def test_clean_summary_removes_spaces_inside_japanese_words():
    assert _clean_summary("土砂災害特別 警報を定 時に発表。 次の文です。") == "土砂災害特別警報を定時に発表。 次の文です。"


def test_only_invalid_articles_are_retried(monkeypatch):
    monkeypatch.setenv("SUMMARY_PROVIDER", "copilot")
    second = dict(ARTICLE, id="article-2", title="Second news")
    calls = []

    def runner(prompt, timeout):
        calls.append(prompt)
        if len(calls) == 1:
            return json.dumps(
                {"summaries": {"article-1": "企業は新サービスを発表しました。医療機関を対象に業務支援機能を提供し、9月5日に運用を始めます。対象地域や料金などの詳細は資料に記載されていません。"}},
                ensure_ascii=False,
            )
        return json.dumps(
            {"summaries": {"article-2": "別の企業が新製品を公開しました。既存製品より処理時間を短縮し、利用者の作業負担を減らすと説明しています。価格と提供地域は資料に記載されていません。"}},
            ensure_ascii=False,
        )

    results = summarize_articles(
        [ARTICLE, second],
        {"summarization": {"minimum_chars": 60, "maximum_attempts": 2}},
        runner=runner,
    )
    assert all(item["summary_method"] == "copilot" for item in results)
    assert "article-1" not in calls[1]
    assert "article-2" in calls[1]
