from content_enricher import _ReadableHTMLParser, _xml_text


def test_html_parser_extracts_description_and_body_but_not_navigation():
    parser = _ReadableHTMLParser()
    parser.feed(
        '<meta name="description" content="記事の説明文です。重要な更新を説明します。">'
        '<meta charset="utf-8">'
        '<nav><p>メニュー項目は除外します。</p></nav>'
        '<main><h1>発表の見出し</h1><p>主体が新制度を発表し、10月から開始します。</p></main>'
    )
    text = parser.text()
    assert "記事の説明文" in text
    assert "10月から開始" in text
    assert "メニュー項目" not in text


def test_xml_parser_extracts_jma_headline_text():
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Report><Head><Title>気象警報・注意報</Title>'
        '<Headline><Text>福岡県では大雨に注意してください。</Text></Headline>'
        '</Head></Report>'
    ).encode()
    text = _xml_text(content)
    assert "気象警報・注意報" in text
    assert "福岡県では大雨" in text
