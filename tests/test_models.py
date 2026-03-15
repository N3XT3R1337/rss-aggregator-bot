import pytest
from sqlalchemy import select

from bot.models import Feed, FeedGroup, Keyword, SentEntry, User, feed_group_association


@pytest.mark.asyncio
async def test_create_user(session):
    user = User(telegram_id=111222333, username="alice")
    session.add(user)
    await session.commit()

    stmt = select(User).where(User.telegram_id == 111222333)
    result = await session.execute(stmt)
    fetched = result.scalar_one()

    assert fetched.username == "alice"
    assert fetched.digest_enabled is False
    assert fetched.is_active is True


@pytest.mark.asyncio
async def test_create_feed_with_user(session, sample_user):
    feed = Feed(user_id=sample_user.id, url="https://example.com/feed.xml", title="Example Feed")
    session.add(feed)
    await session.commit()

    stmt = select(Feed).where(Feed.user_id == sample_user.id)
    result = await session.execute(stmt)
    fetched = result.scalar_one()

    assert fetched.url == "https://example.com/feed.xml"
    assert fetched.title == "Example Feed"
    assert fetched.is_active is True
    assert fetched.error_count == 0


@pytest.mark.asyncio
async def test_feed_group_association(session, sample_user):
    feed = Feed(user_id=sample_user.id, url="https://example.com/rss", title="Test")
    group = FeedGroup(user_id=sample_user.id, name="Tech")
    session.add_all([feed, group])
    await session.flush()

    group.feeds.append(feed)
    await session.commit()

    stmt = select(FeedGroup).where(FeedGroup.id == group.id)
    result = await session.execute(stmt)
    fetched_group = result.scalar_one()
    await session.refresh(fetched_group, ["feeds"])

    assert len(fetched_group.feeds) == 1
    assert fetched_group.feeds[0].url == "https://example.com/rss"


@pytest.mark.asyncio
async def test_keyword_creation(session, sample_user):
    kw_include = Keyword(user_id=sample_user.id, word="python", is_include=True)
    kw_exclude = Keyword(user_id=sample_user.id, word="spam", is_include=False)
    session.add_all([kw_include, kw_exclude])
    await session.commit()

    stmt = select(Keyword).where(Keyword.user_id == sample_user.id).order_by(Keyword.word)
    result = await session.execute(stmt)
    keywords = list(result.scalars().all())

    assert len(keywords) == 2
    assert keywords[0].word == "python"
    assert keywords[0].is_include is True
    assert keywords[1].word == "spam"
    assert keywords[1].is_include is False


@pytest.mark.asyncio
async def test_sent_entry_tracking(session, sample_user):
    feed = Feed(user_id=sample_user.id, url="https://example.com/rss", title="Test")
    session.add(feed)
    await session.flush()

    entry = SentEntry(
        user_id=sample_user.id,
        feed_id=feed.id,
        entry_id="abc123hash",
        entry_title="Test Article",
        entry_url="https://example.com/article/1",
    )
    session.add(entry)
    await session.commit()

    stmt = select(SentEntry).where(SentEntry.entry_id == "abc123hash")
    result = await session.execute(stmt)
    fetched = result.scalar_one()

    assert fetched.entry_title == "Test Article"
    assert fetched.user_id == sample_user.id
