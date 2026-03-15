import pytest
from unittest.mock import patch, MagicMock

from bot.models import Keyword
from bot.services.feed_service import (
    entry_matches_keywords,
    generate_entry_id,
    format_entry_message,
    parse_entry_date,
)


def test_generate_entry_id_consistency():
    entry = {"id": "unique-123", "link": "https://example.com", "title": "Test"}
    id1 = generate_entry_id(entry)
    id2 = generate_entry_id(entry)
    assert id1 == id2
    assert len(id1) == 64


def test_generate_entry_id_different_entries():
    entry1 = {"id": "abc", "link": "", "title": ""}
    entry2 = {"id": "xyz", "link": "", "title": ""}
    assert generate_entry_id(entry1) != generate_entry_id(entry2)


def test_entry_matches_no_keywords():
    entry = {"title": "Python News", "summary": "Latest updates"}
    assert entry_matches_keywords(entry, []) is True


def test_entry_matches_include_keyword():
    kw = MagicMock(spec=Keyword)
    kw.word = "python"
    kw.is_include = True

    entry_match = {"title": "Python Tutorial", "summary": "Learn Python"}
    entry_no_match = {"title": "Java Tutorial", "summary": "Learn Java"}

    assert entry_matches_keywords(entry_match, [kw]) is True
    assert entry_matches_keywords(entry_no_match, [kw]) is False


def test_entry_matches_exclude_keyword():
    kw = MagicMock(spec=Keyword)
    kw.word = "spam"
    kw.is_include = False

    entry_spam = {"title": "Buy Spam Now", "summary": "Great deals"}
    entry_clean = {"title": "Python News", "summary": "Great updates"}

    assert entry_matches_keywords(entry_spam, [kw]) is False
    assert entry_matches_keywords(entry_clean, [kw]) is True


def test_entry_matches_mixed_keywords():
    kw_include = MagicMock(spec=Keyword)
    kw_include.word = "python"
    kw_include.is_include = True

    kw_exclude = MagicMock(spec=Keyword)
    kw_exclude.word = "advertisement"
    kw_exclude.is_include = False

    entry_good = {"title": "Python Framework Released", "summary": "New framework"}
    entry_excluded = {"title": "Python Advertisement", "summary": "Buy now"}
    entry_irrelevant = {"title": "Java News", "summary": "Updates"}

    assert entry_matches_keywords(entry_good, [kw_include, kw_exclude]) is True
    assert entry_matches_keywords(entry_excluded, [kw_include, kw_exclude]) is False
    assert entry_matches_keywords(entry_irrelevant, [kw_include, kw_exclude]) is False


def test_format_entry_message():
    entry = {
        "title": "Test Article",
        "link": "https://example.com/article",
        "summary": "This is a test summary.",
        "feed_title": "Test Feed",
    }
    msg = format_entry_message(entry)

    assert "<b>Test Article</b>" in msg
    assert "Test Feed" in msg
    assert "This is a test summary." in msg
    assert 'href="https://example.com/article"' in msg


def test_format_entry_message_long_summary():
    entry = {
        "title": "Long Article",
        "link": "",
        "summary": "x" * 500,
        "feed_title": "Feed",
    }
    msg = format_entry_message(entry)
    assert "..." in msg


def test_parse_entry_date_none():
    assert parse_entry_date({}) is None
    assert parse_entry_date({"published_parsed": None}) is None
