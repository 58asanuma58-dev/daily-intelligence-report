import json

import pytest

from summarizer import _parse_response, summarize_articles


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
