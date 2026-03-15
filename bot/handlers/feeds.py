from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.database import async_session
from bot.services.feed_service import (
    add_feed,
    get_or_create_user,
    list_feeds,
    remove_feed,
    toggle_feed,
)

router = Router()


@router.message(Command("add"))
async def cmd_add_feed(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /add <feed_url>")
        return

    url = command.args.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        feed, created = await add_feed(session, user, url)

        if created:
            await message.answer(f"✅ Feed added: <b>{feed.title}</b>", parse_mode="HTML")
        else:
            await message.answer(f"ℹ️ Feed already exists: <b>{feed.title}</b>", parse_mode="HTML")


@router.message(Command("list"))
async def cmd_list_feeds(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        feeds = await list_feeds(session, user)

        if not feeds:
            await message.answer("You have no feeds. Use /add <url> to add one.")
            return

        lines = ["<b>📋 Your Feeds:</b>\n"]
        for i, feed in enumerate(feeds, 1):
            status = "✅" if feed.is_active else "⏸️"
            lines.append(f"{i}. {status} <b>{feed.title}</b>\n   ID: {feed.id} | {feed.url}")

        await message.answer("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


@router.message(Command("remove"))
async def cmd_remove_feed(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /remove <feed_id>")
        return

    try:
        feed_id = int(command.args.strip())
    except ValueError:
        await message.answer("Feed ID must be a number.")
        return

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        removed = await remove_feed(session, user, feed_id)

        if removed:
            await message.answer("✅ Feed removed successfully.")
        else:
            await message.answer("❌ Feed not found or doesn't belong to you.")


@router.message(Command("toggle"))
async def cmd_toggle_feed(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /toggle <feed_id>")
        return

    try:
        feed_id = int(command.args.strip())
    except ValueError:
        await message.answer("Feed ID must be a number.")
        return

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        feed = await toggle_feed(session, user, feed_id)

        if feed:
            status = "active" if feed.is_active else "paused"
            await message.answer(f"✅ Feed <b>{feed.title}</b> is now {status}.", parse_mode="HTML")
        else:
            await message.answer("❌ Feed not found.")


@router.message(Command("check"))
async def cmd_check_feeds(message: Message):
    from bot.services.feed_service import fetch_feed_entries, format_entry_message

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        feeds = await list_feeds(session, user)
        active_feeds = [f for f in feeds if f.is_active]

        if not active_feeds:
            await message.answer("No active feeds to check.")
            return

        await message.answer(f"🔄 Checking {len(active_feeds)} feeds...")

        total = 0
        from sqlalchemy import select
        from bot.models import Keyword
        stmt = select(Keyword).where(Keyword.user_id == user.id)
        result = await session.execute(stmt)
        keywords = list(result.scalars().all())

        for feed in active_feeds:
            entries = await fetch_feed_entries(session, feed, keywords)
            for entry in entries:
                msg = format_entry_message(entry)
                await message.answer(msg, parse_mode="HTML", disable_web_page_preview=True)
                total += 1

        if total == 0:
            await message.answer("No new entries found.")
        else:
            await message.answer(f"✅ Found {total} new entries.")
