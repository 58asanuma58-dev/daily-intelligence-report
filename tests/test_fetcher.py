from types import SimpleNamespace

import fetcher


class FakeResponse:
    content = b"feed"

    def raise_for_status(self):
        return None


def test_first_undated_item_can_use_feed_update_time(monkeypatch):
    parsed_feed = SimpleNamespace(
        feed={"updated": "Wed, 19 Aug 2026 04:36:55 +0000"},
        entries=[
            {"title": "最新記事", "link": "https://example.com/new"},
            {"title": "過去記事", "link": "https://example.com/old"},
        ],
    )
    monkeypatch.setattr(fetcher.requests, "get", lambda *args, **kwargs: FakeResponse())
    monkeypatch.setattr(fetcher.feedparser, "parse", lambda content: parsed_feed)

    articles = fetcher.fetch_feed(
        {
            "name": "日付なしRSS",
            "url": "https://example.com/feed",
            "use_feed_date_for_first_undated_item": True,
        },
        max_items=2,
    )

    assert articles[0]["published_at"] == "Wed, 19 Aug 2026 04:36:55 +0000"
    assert articles[1]["published_at"] == "不明"


def test_feed_update_time_is_not_used_without_explicit_setting(monkeypatch):
    parsed_feed = SimpleNamespace(
        feed={"updated": "Wed, 19 Aug 2026 04:36:55 +0000"},
        entries=[{"title": "記事", "link": "https://example.com/item"}],
    )
    monkeypatch.setattr(fetcher.requests, "get", lambda *args, **kwargs: FakeResponse())
    monkeypatch.setattr(fetcher.feedparser, "parse", lambda content: parsed_feed)

    articles = fetcher.fetch_feed(
        {"name": "通常RSS", "url": "https://example.com/feed"},
        max_items=1,
    )

    assert articles[0]["published_at"] == "不明"
