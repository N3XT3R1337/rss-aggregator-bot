import logging
from datetime import datetime
from typing import Optional

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.config import settings
from bot.database import async_session
from bot.models import Feed, Keyword, User
from bot.services.feed_service import fetch_feed_entries, format_entry_message
from bot.services.digest_service import build_digest, format_digest_message

logger = logging.getLogger(__name__)

scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler


async def check_feeds_job(bot: Bot):
    async with async_session() as session:
        stmt = (
            select(User)
            .where(User.is_active == True)
            .options(selectinload(User.feeds), selectinload(User.keywords))
        )
        result = await session.execute(stmt)
        users = result.scalars().all()

        for user in users:
            if user.digest_enabled:
                continue

            active_feeds = [f for f in user.feeds if f.is_active]
            for feed in active_feeds:
                try:
                    entries = await fetch_feed_entries(session, feed, list(user.keywords))
                    for entry in entries:
                        msg = format_entry_message(entry)
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=msg,
                            parse_mode="HTML",
                            disable_web_page_preview=True,
                        )
                except Exception as e:
                    logger.error(f"Error checking feed {feed.url} for user {user.telegram_id}: {e}")


async def send_digests_job(bot: Bot):
    now = datetime.utcnow()
    async with async_session() as session:
        stmt = (
            select(User)
            .where(
                User.is_active == True,
                User.digest_enabled == True,
                User.digest_hour == now.hour,
            )
            .options(selectinload(User.feeds), selectinload(User.keywords))
        )
        result = await session.execute(stmt)
        users = result.scalars().all()

        for user in users:
            try:
                active_feeds = [f for f in user.feeds if f.is_active]
                all_entries = []
                for feed in active_feeds:
                    entries = await fetch_feed_entries(session, feed, list(user.keywords))
                    all_entries.extend(entries)

                if all_entries:
                    digest = build_digest(all_entries)
                    msg = format_digest_message(digest)
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=msg,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
            except Exception as e:
                logger.error(f"Error sending digest to user {user.telegram_id}: {e}")


def setup_scheduler(bot: Bot):
    sched = get_scheduler()

    sched.add_job(
        check_feeds_job,
        IntervalTrigger(minutes=settings.check_interval_minutes),
        args=[bot],
        id="check_feeds",
        replace_existing=True,
        max_instances=1,
    )

    sched.add_job(
        send_digests_job,
        CronTrigger(minute=0),
        args=[bot],
        id="send_digests",
        replace_existing=True,
        max_instances=1,
    )

    sched.start()
    logger.info("Scheduler started with feed check interval: %d minutes", settings.check_interval_minutes)


def shutdown_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        scheduler = None
