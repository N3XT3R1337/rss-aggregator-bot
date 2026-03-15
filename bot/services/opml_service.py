import xml.etree.ElementTree as ET
from typing import List, Tuple
from io import BytesIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models import Feed, FeedGroup, User, feed_group_association


def generate_opml(feeds: List[Feed], groups: List[FeedGroup]) -> str:
    opml = ET.Element("opml", version="2.0")
    head = ET.SubElement(opml, "head")
    title_el = ET.SubElement(head, "title")
    title_el.text = "RSS Aggregator Bot Subscriptions"
    body = ET.SubElement(opml, "body")

    grouped_feeds = set()
    for group in groups:
        if group.feeds:
            outline = ET.SubElement(body, "outline", text=group.name, title=group.name)
            for feed in group.feeds:
                ET.SubElement(
                    outline,
                    "outline",
                    type="rss",
                    text=feed.title or feed.url,
                    title=feed.title or feed.url,
                    xmlUrl=feed.url,
                )
                grouped_feeds.add(feed.id)

    for feed in feeds:
        if feed.id not in grouped_feeds:
            ET.SubElement(
                body,
                "outline",
                type="rss",
                text=feed.title or feed.url,
                title=feed.title or feed.url,
                xmlUrl=feed.url,
            )

    tree = ET.ElementTree(opml)
    buffer = BytesIO()
    tree.write(buffer, encoding="unicode", xml_declaration=True)
    return buffer.getvalue()


def parse_opml(content: str) -> List[Tuple[str, str, str]]:
    root = ET.fromstring(content)
    feeds = []

    def extract_feeds(element, group_name=""):
        for outline in element.findall("outline"):
            xml_url = outline.get("xmlUrl")
            if xml_url:
                title = outline.get("title") or outline.get("text") or xml_url
                feeds.append((xml_url, title, group_name))
            else:
                child_group = outline.get("title") or outline.get("text") or ""
                extract_feeds(outline, child_group)

    body = root.find("body")
    if body is not None:
        extract_feeds(body)

    return feeds


async def import_opml(
    session: AsyncSession, user: User, content: str
) -> Tuple[int, int, int]:
    feed_data = parse_opml(content)
    added = 0
    skipped = 0
    groups_created = 0

    group_cache = {}

    for url, title, group_name in feed_data:
        stmt = select(Feed).where(Feed.user_id == user.id, Feed.url == url)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            skipped += 1
            feed = existing
        else:
            feed = Feed(user_id=user.id, url=url, title=title)
            session.add(feed)
            await session.flush()
            added += 1

        if group_name:
            if group_name not in group_cache:
                stmt = select(FeedGroup).where(
                    FeedGroup.user_id == user.id, FeedGroup.name == group_name
                )
                result = await session.execute(stmt)
                group = result.scalar_one_or_none()
                if group is None:
                    group = FeedGroup(user_id=user.id, name=group_name)
                    session.add(group)
                    await session.flush()
                    groups_created += 1
                group_cache[group_name] = group

            group = group_cache[group_name]
            if feed not in group.feeds:
                group.feeds.append(feed)

    await session.commit()
    return added, skipped, groups_created


async def export_opml(session: AsyncSession, user: User) -> str:
    stmt = select(Feed).where(Feed.user_id == user.id)
    result = await session.execute(stmt)
    feeds = list(result.scalars().all())

    stmt = select(FeedGroup).where(FeedGroup.user_id == user.id)
    result = await session.execute(stmt)
    groups = list(result.scalars().all())

    for group in groups:
        await session.refresh(group, ["feeds"])

    return generate_opml(feeds, groups)
