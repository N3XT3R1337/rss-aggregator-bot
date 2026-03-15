import asyncio
import hashlib
from datetime import datetime
from typing import List, Optional, Tuple
from time import mktime

import feedparser
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models import Feed, Keyword, SentEntry, User


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: Optional[str] = None) -> User:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def add_feed(session: AsyncSession, user: User, url: str) -> Tuple[Feed, bool]:
    stmt = select(Feed).where(Feed.user_id == user.id, Feed.url == url)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing, False

    parsed = await asyncio.to_thread(feedparser.parse, url)
    title = parsed.feed.get("title", url) if parsed.feed else url

    feed = Feed(user_id=user.id, url=url, title=title)
    session.add(feed)
    await session.commit()
    await session.refresh(feed)
    return feed, True


async def remove_feed(session: AsyncSession, user: User, feed_id: int) -> bool:
    stmt = select(Feed).where(Feed.id == feed_id, Feed.user_id == user.id)
    result = await session.execute(stmt)
    feed = result.scalar_one_or_none()
    if feed is None:
        return False
    await session.delete(feed)
    await session.commit()
    return True


async def list_feeds(session: AsyncSession, user: User) -> List[Feed]:
    stmt = select(Feed).where(Feed.user_id == user.id).order_by(Feed.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def toggle_feed(session: AsyncSession, user: User, feed_id: int) -> Optional[Feed]:
    stmt = select(Feed).where(Feed.id == feed_id, Feed.user_id == user.id)
    result = await session.execute(stmt)
    feed = result.scalar_one_or_none()
    if feed is None:
        return None
    feed.is_active = not feed.is_active
    await session.commit()
    await session.refresh(feed)
    return feed


def generate_entry_id(entry) -> str:
    entry_id = entry.get("id", "") or entry.get("link", "") or entry.get("title", "")
    return hashlib.sha256(entry_id.encode("utf-8")).hexdigest()


def entry_matches_keywords(entry, keywords: List[Keyword]) -> bool:
    if not keywords:
        return True

    include_keywords = [k for k in keywords if k.is_include]
    exclude_keywords = [k for k in keywords if not k.is_include]

    text = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()

    for kw in exclude_keywords:
        if kw.word.lower() in text:
            return False

    if not include_keywords:
        return True

    for kw in include_keywords:
        if kw.word.lower() in text:
            return True

    return False


def parse_entry_date(entry) -> Optional[datetime]:
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)
        if parsed:
            try:
                return datetime.fromtimestamp(mktime(parsed))
            except (ValueError, OverflowError, TypeError):
                continue
    return None


async def fetch_feed_entries(session: AsyncSession, feed: Feed, keywords: List[Keyword]) -> List[dict]:
    parsed = await asyncio.to_thread(feedparser.parse, feed.url)

    if parsed.bozo and not parsed.entries:
        feed.error_count += 1
        await session.commit()
        return []

    feed.error_count = 0
    feed.last_checked = datetime.utcnow()

    new_entries = []
    for entry in parsed.entries[:10]:
        entry_hash = generate_entry_id(entry)

        stmt = select(SentEntry).where(
            SentEntry.user_id == feed.user_id,
            SentEntry.entry_id == entry_hash,
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            continue

        if not entry_matches_keywords(entry, keywords):
            continue

        entry_date = parse_entry_date(entry)
        entry_data = {
            "title": entry.get("title", "No title"),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "published": entry_date,
            "feed_title": feed.title,
            "entry_hash": entry_hash,
        }
        new_entries.append(entry_data)

        sent = SentEntry(
            user_id=feed.user_id,
            feed_id=feed.id,
            entry_id=entry_hash,
            entry_title=entry_data["title"],
            entry_url=entry_data["link"],
        )
        session.add(sent)

    if new_entries:
        latest = max((e["published"] for e in new_entries if e["published"]), default=None)
        if latest:
            feed.last_entry_date = latest

    await session.commit()
    return new_entries


def format_entry_message(entry: dict) -> str:
    parts = [f"<b>{entry['title']}</b>"]
    if entry.get("feed_title"):
        parts.append(f"📡 {entry['feed_title']}")
    if entry.get("summary"):
        summary = entry["summary"][:300]
        if len(entry["summary"]) > 300:
            summary += "..."
        parts.append(summary)
    if entry.get("link"):
        parts.append(f'<a href="{entry["link"]}">Read more</a>')
    return "\n\n".join(parts)
