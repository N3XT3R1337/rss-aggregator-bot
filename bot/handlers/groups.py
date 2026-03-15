from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.database import async_session
from bot.models import Feed, FeedGroup
from bot.services.feed_service import get_or_create_user

router = Router()


@router.message(Command("newgroup"))
async def cmd_new_group(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /newgroup <group_name>")
        return

    name = command.args.strip()
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        stmt = select(FeedGroup).where(FeedGroup.user_id == user.id, FeedGroup.name == name)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            await message.answer(f"Group <b>{name}</b> already exists.", parse_mode="HTML")
            return

        group = FeedGroup(user_id=user.id, name=name)
        session.add(group)
        await session.commit()
        await message.answer(f"✅ Group <b>{name}</b> created.", parse_mode="HTML")


@router.message(Command("groups"))
async def cmd_list_groups(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        stmt = (
            select(FeedGroup)
            .where(FeedGroup.user_id == user.id)
            .options(selectinload(FeedGroup.feeds))
            .order_by(FeedGroup.name)
        )
        result = await session.execute(stmt)
        groups = list(result.scalars().all())

        if not groups:
            await message.answer("No groups. Use /newgroup <name> to create one.")
            return

        lines = ["<b>📁 Your Groups:</b>\n"]
        for group in groups:
            feed_count = len(group.feeds)
            feed_names = ", ".join(f.title or f.url for f in group.feeds[:3])
            if len(group.feeds) > 3:
                feed_names += f" +{len(group.feeds) - 3} more"
            lines.append(f"• <b>{group.name}</b> (ID: {group.id}) — {feed_count} feeds")
            if feed_names:
                lines.append(f"  {feed_names}")

        await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("addtogroup"))
async def cmd_add_to_group(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) < 2:
        await message.answer("Usage: /addtogroup <group_id> <feed_id>")
        return

    parts = command.args.strip().split()
    try:
        group_id = int(parts[0])
        feed_id = int(parts[1])
    except ValueError:
        await message.answer("Both group_id and feed_id must be numbers.")
        return

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        stmt = select(FeedGroup).where(FeedGroup.user_id == user.id, FeedGroup.id == group_id).options(selectinload(FeedGroup.feeds))
        result = await session.execute(stmt)
        group = result.scalar_one_or_none()

        if not group:
            await message.answer("❌ Group not found.")
            return

        stmt = select(Feed).where(Feed.user_id == user.id, Feed.id == feed_id)
        result = await session.execute(stmt)
        feed = result.scalar_one_or_none()

        if not feed:
            await message.answer("❌ Feed not found.")
            return

        if feed in group.feeds:
            await message.answer("Feed is already in this group.")
            return

        group.feeds.append(feed)
        await session.commit()
        await message.answer(
            f"✅ Added <b>{feed.title}</b> to group <b>{group.name}</b>.",
            parse_mode="HTML",
        )


@router.message(Command("rmfromgroup"))
async def cmd_remove_from_group(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) < 2:
        await message.answer("Usage: /rmfromgroup <group_id> <feed_id>")
        return

    parts = command.args.strip().split()
    try:
        group_id = int(parts[0])
        feed_id = int(parts[1])
    except ValueError:
        await message.answer("Both group_id and feed_id must be numbers.")
        return

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        stmt = select(FeedGroup).where(FeedGroup.user_id == user.id, FeedGroup.id == group_id).options(selectinload(FeedGroup.feeds))
        result = await session.execute(stmt)
        group = result.scalar_one_or_none()

        if not group:
            await message.answer("❌ Group not found.")
            return

        stmt = select(Feed).where(Feed.user_id == user.id, Feed.id == feed_id)
        result = await session.execute(stmt)
        feed = result.scalar_one_or_none()

        if not feed:
            await message.answer("❌ Feed not found.")
            return

        if feed in group.feeds:
            group.feeds.remove(feed)
            await session.commit()
            await message.answer(
                f"✅ Removed <b>{feed.title}</b> from group <b>{group.name}</b>.",
                parse_mode="HTML",
            )
        else:
            await message.answer("Feed is not in this group.")


@router.message(Command("delgroup"))
async def cmd_delete_group(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /delgroup <group_id>")
        return

    try:
        group_id = int(command.args.strip())
    except ValueError:
        await message.answer("Group ID must be a number.")
        return

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        stmt = select(FeedGroup).where(FeedGroup.user_id == user.id, FeedGroup.id == group_id)
        result = await session.execute(stmt)
        group = result.scalar_one_or_none()

        if not group:
            await message.answer("❌ Group not found.")
            return

        name = group.name
        await session.delete(group)
        await session.commit()
        await message.answer(f"✅ Group <b>{name}</b> deleted.", parse_mode="HTML")
