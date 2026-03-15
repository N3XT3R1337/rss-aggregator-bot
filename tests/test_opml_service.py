import pytest

from bot.services.opml_service import generate_opml, parse_opml
from bot.models import Feed, FeedGroup


def _make_feed(id_, url, title, user_id=1):
    feed = Feed.__new__(Feed)
    feed.id = id_
    feed.url = url
    feed.title = title
    feed.user_id = user_id
    return feed


def _make_group(id_, name, feeds, user_id=1):
    group = FeedGroup.__new__(FeedGroup)
    group.id = id_
    group.name = name
    group.feeds = feeds
    group.user_id = user_id
    return group


def test_generate_opml_basic():
    feeds = [
        _make_feed(1, "https://example.com/rss", "Example"),
        _make_feed(2, "https://news.com/feed", "News"),
    ]
    result = generate_opml(feeds, [])

    assert "Example" in result
    assert "https://example.com/rss" in result
    assert "https://news.com/feed" in result
    assert "opml" in result.lower()


def test_generate_opml_with_groups():
    feed1 = _make_feed(1, "https://tech.com/rss", "Tech News")
    feed2 = _make_feed(2, "https://sci.com/feed", "Science")
    group = _make_group(1, "Technology", [feed1])

    result = generate_opml([feed1, feed2], [group])

    assert "Technology" in result
    assert "Tech News" in result
    assert "Science" in result


def test_parse_opml_basic():
    opml_content = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head><title>Test</title></head>
  <body>
    <outline type="rss" text="Example" title="Example" xmlUrl="https://example.com/rss"/>
    <outline text="Tech" title="Tech">
      <outline type="rss" text="TechFeed" title="TechFeed" xmlUrl="https://tech.com/feed"/>
    </outline>
  </body>
</opml>"""

    feeds = parse_opml(opml_content)
    assert len(feeds) == 2

    urls = [f[0] for f in feeds]
    assert "https://example.com/rss" in urls
    assert "https://tech.com/feed" in urls

    tech_feed = [f for f in feeds if f[0] == "https://tech.com/feed"][0]
    assert tech_feed[2] == "Tech"


def test_parse_opml_empty():
    opml_content = """<?xml version="1.0"?>
<opml version="2.0">
  <head><title>Empty</title></head>
  <body></body>
</opml>"""

    feeds = parse_opml(opml_content)
    assert len(feeds) == 0


def test_roundtrip_opml():
    feeds = [
        _make_feed(1, "https://a.com/rss", "Feed A"),
        _make_feed(2, "https://b.com/rss", "Feed B"),
    ]
    group = _make_group(1, "My Group", [feeds[0]])

    exported = generate_opml(feeds, [group])
    parsed = parse_opml(exported)

    assert len(parsed) == 2
    urls = {f[0] for f in parsed}
    assert "https://a.com/rss" in urls
    assert "https://b.com/rss" in urls
