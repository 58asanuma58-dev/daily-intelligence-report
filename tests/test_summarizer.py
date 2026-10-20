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


def test_required_mode_accepts_summary_with_surrounding_metadata(monkeypatch):
    monkeypatch.setenv("SUMMARY_PROVIDER", "copilot")
    monkeypatch.setenv("SUMMARY_REQUIRED", "true")
    summary = "企業は9月5日、病院向けの新サービスを発表しました。対象となる医療機関の業務を支援する機能を提供する内容です。詳細な提供地域や価格は資料に記載されていません。"
    response = (
        '{"status":"complete"}\n```json\n'
        + json.dumps({"summaries": {"article-1": summary}}, ensure_ascii=False)
        + '\n```\n{"usage":1}'
    )
    result = summarize_articles(
        [ARTICLE], {"summarization": {"minimum_chars": 60}},
        runner=lambda prompt, timeout: response,
    )[0]
    assert result["summary"] == summary
    assert result["summary_method"] == "copilot"


def test_parser_accepts_unescaped_newline_from_cli():
    response = '{"summaries":{"article-1":"1文目です。\n2文目です。"}}'
    assert _parse_response(response)["article-1"] == "1文目です。 2文目です。"


@pytest.mark.parametrize("wrapper", [
    "{}",
    "```json\n{}\n```",
    "要約結果です。\n{}\n以上です。",
    "[INFO] Summary ready\n{}\nSee [source] for details.",
    "[注記] 要約結果です。\n{}\n[出典]を確認してください。",
    '{{"status":"complete"}}\n{}\n{{"usage":1}}',
    '[{{"status":"complete"}}]\n{}\n{{"usage":1}}',
])
def test_parser_accepts_one_summary_document_with_surrounding_output(wrapper):
    payload = {"summaries": {"article-1": '値は {例} と [例]、"引用"、C:\\tmpです。'}}
    response = wrapper.format(json.dumps(payload, ensure_ascii=False))
    assert _parse_response(response, {"article-1"}) == payload["summaries"]


@pytest.mark.parametrize("second", [
    {"article-2": "別の記事です。"},
    {"article-1": "最初の要約です。"},
    {"article-1": "変更した要約です。"},
])
def test_parser_rejects_multiple_summary_documents(second):
    first = json.dumps({"summaries": {"article-1": "最初の要約です。"}})
    response = first + "\n```json\n" + json.dumps({"summaries": second}) + "\n```"
    with pytest.raises(ValueError, match="複数"):
        _parse_response(response, {"article-1", "article-2"})


@pytest.mark.parametrize("response", [
    '{"summaries":{},"summaries":{"article-1":"要約です。"}}',
    '{"summaries":{"article-1":"最初です。","article-1":"変更です。"}}',
])
def test_parser_rejects_duplicate_json_keys(response):
    with pytest.raises(ValueError, match="重複"):
        _parse_response(response)


@pytest.mark.parametrize("value", [None, 1, True, ["日本語の要約です。"], {"text": "要約です。"}])
def test_parser_rejects_non_string_summaries(value):
    response = json.dumps({"summaries": {"article-1": value}})
    with pytest.raises(ValueError, match="文字列"):
        _parse_response(response)


@pytest.mark.parametrize("response", [
    "要約はありません。",
    '{"usage":1}',
    '[{"summaries":{"article-1":"要約です。"}}]',
    '{"metadata":{"summaries":{"article-1":"要約です。"}}}',
    '{"summaries":[]}',
    '{"summaries":null}',
    '{"broken":{"summaries":{"article-1":"要約です。"}}',
    '{"summaries":{"article-1":"要約です。"}}\n{"summaries":',
    '{"summaries":\n{"summaries":{"article-1":"要約です。"}}',
    '[broken {"summaries":{"article-1":"要約です。"}}]',
    '[INFO\n{"summaries":{"article-1":"要約です。"}}',
])
def test_parser_rejects_missing_nested_or_malformed_summary_documents(response):
    with pytest.raises(ValueError):
        _parse_response(response, {"article-1"})


def test_parser_checks_requested_ids_but_allows_partial_results():
    response = '{"summaries":{"article-1":"要約です。"}}'
    assert _parse_response(response, {"article-1", "article-2"}) == {"article-1": "要約です。"}
    with pytest.raises(ValueError, match="記事ID"):
        _parse_response(response, {"article-2"})
    assert _parse_response('{"summaries":{}}', {"article-1"}) == {}


def test_parser_does_not_expose_response_content_in_error():
    response = '{"summaries":{"article-1":"private response text"}'
    with pytest.raises(ValueError) as error:
        _parse_response(response)
    assert "private response text" not in str(error.value)


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


def test_valid_cached_summary_skips_copilot_call(monkeypatch):
    monkeypatch.setenv("SUMMARY_PROVIDER", "copilot")
    cached = {
        "article-1": "企業は9月5日、病院向けの新サービスを発表しました。対象となる医療機関の業務を支援する機能を提供する内容です。詳細な提供地域や価格は資料に記載されていません。"
    }

    def runner(prompt, timeout):
        raise AssertionError("有効なキャッシュがある記事を再要約してはいけません")

    result = summarize_articles(
        [ARTICLE], {"summarization": {"minimum_chars": 60}},
        runner=runner, cached_summaries=cached,
    )[0]
    assert result["summary_method"] == "copilot"
    assert result["summary"].startswith("企業は9月5日")


def test_retry_cannot_overwrite_a_previously_accepted_summary(monkeypatch):
    monkeypatch.setenv("SUMMARY_PROVIDER", "copilot")
    monkeypatch.setenv("SUMMARY_REQUIRED", "true")
    summary = "企業は新サービスを発表しました。医療機関を対象に業務支援機能を提供し、9月5日に運用を始めます。対象地域や料金などの詳細は資料に記載されていません。"
    calls = []

    def runner(prompt, timeout):
        calls.append(prompt)
        # 2回目に依頼されていないarticle-1を上書きする応答は受け入れない。
        summaries = {"article-1": summary}
        if len(calls) == 2:
            summaries["article-2"] = summary
        return json.dumps({"summaries": summaries})

    with pytest.raises(RuntimeError, match="品質条件"):
        summarize_articles(
            [ARTICLE, dict(ARTICLE, id="article-2")],
            {"summarization": {"minimum_chars": 60, "maximum_attempts": 2}},
            runner=runner,
        )
    assert len(calls) == 2
    assert "article-1" not in calls[1]


@pytest.mark.parametrize("response", [
    '{"summaries":{"article-1":"短すぎます。"}}\n{"usage":1}',
    '{"summaries":{"wrong-id":"要約です。"}}',
    '{"summaries":',
])
def test_required_mode_still_rejects_invalid_responses(monkeypatch, response):
    monkeypatch.setenv("SUMMARY_PROVIDER", "copilot")
    monkeypatch.setenv("SUMMARY_REQUIRED", "true")
    calls = []

    def runner(prompt, timeout):
        calls.append(prompt)
        return response

    with pytest.raises(RuntimeError):
        summarize_articles(
            [ARTICLE], {"summarization": {"minimum_chars": 60, "maximum_attempts": 2}},
            runner=runner,
        )
    assert len(calls) == 2
