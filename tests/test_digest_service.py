from datetime import datetime

from bot.services.digest_service import build_digest, format_digest_message, format_digest_stats


def test_build_digest_groups_by_feed():
    entries = [
        {"title": "Article 1", "feed_title": "Feed A", "published": datetime(2025, 1, 1)},
        {"title": "Article 2", "feed_title": "Feed B", "published": datetime(2025, 1, 2)},
        {"title": "Article 3", "feed_title": "Feed A", "published": datetime(2025, 1, 3)},
    ]

    digest = build_digest(entries)
    assert len(digest) == 2
    assert len(digest["Feed A"]) == 2
    assert len(digest["Feed B"]) == 1


def test_build_digest_sorts_by_date():
    entries = [
        {"title": "Old", "feed_title": "Feed", "published": datetime(2025, 1, 1)},
        {"title": "New", "feed_title": "Feed", "published": datetime(2025, 6, 1)},
        {"title": "Mid", "feed_title": "Feed", "published": datetime(2025, 3, 1)},
    ]

    digest = build_digest(entries)
    titles = [e["title"] for e in digest["Feed"]]
    assert titles == ["New", "Mid", "Old"]


def test_format_digest_message_empty():
    msg = format_digest_message({})
    assert "No new entries" in msg


def test_format_digest_message_with_entries():
    digest = {
        "Tech Blog": [
            {"title": "AI Update", "link": "https://example.com/ai"},
            {"title": "Python 4", "link": "https://example.com/py4"},
        ],
        "News": [
            {"title": "Breaking News", "link": "https://example.com/news"},
        ],
    }
    msg = format_digest_message(digest)

    assert "3 new entries" in msg
    assert "Tech Blog" in msg
    assert "News" in msg
    assert "AI Update" in msg
    assert "Breaking News" in msg


def test_format_digest_stats():
    digest = {
        "Feed A": [{"title": "a1"}, {"title": "a2"}],
        "Feed B": [{"title": "b1"}],
    }
    stats = format_digest_stats(digest)

    assert "Feeds with updates: 2" in stats
    assert "Total new entries: 3" in stats
    assert "Feed A: 2 entries" in stats
    assert "Feed B: 1 entries" in stats
