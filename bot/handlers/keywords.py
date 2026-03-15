from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from sqlalchemy import select

from bot.database import async_session
from bot.models import Keyword
from bot.services.feed_service import get_or_create_user

router = Router()


@router.message(Command("addkw"))
async def cmd_add_keyword(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /addkw <keyword>\nPrefix with - to exclude (e.g., /addkw -spam)")
        return

    word = command.args.strip()
    is_include = True

    if word.startswith("-"):
        word = word[1:].strip()
        is_include = False

    if not word:
        await message.answer("Keyword cannot be empty.")
        return

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        stmt = select(Keyword).where(Keyword.user_id == user.id, Keyword.word == word)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.is_include = is_include
            await session.commit()
            mode = "include" if is_include else "exclude"
            await message.answer(f"✅ Keyword <b>{word}</b> updated to {mode}.", parse_mode="HTML")
        else:
            kw = Keyword(user_id=user.id, word=word, is_include=is_include)
            session.add(kw)
            await session.commit()
            mode = "include" if is_include else "exclude"
            await message.answer(f"✅ Keyword <b>{word}</b> added as {mode}.", parse_mode="HTML")


@router.message(Command("rmkw"))
async def cmd_remove_keyword(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /rmkw <keyword>")
        return

    word = command.args.strip()

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        stmt = select(Keyword).where(Keyword.user_id == user.id, Keyword.word == word)
        result = await session.execute(stmt)
        kw = result.scalar_one_or_none()

        if kw:
            await session.delete(kw)
            await session.commit()
            await message.answer(f"✅ Keyword <b>{word}</b> removed.", parse_mode="HTML")
        else:
            await message.answer(f"❌ Keyword <b>{word}</b> not found.", parse_mode="HTML")


@router.message(Command("keywords"))
async def cmd_list_keywords(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        stmt = select(Keyword).where(Keyword.user_id == user.id).order_by(Keyword.word)
        result = await session.execute(stmt)
        keywords = list(result.scalars().all())

        if not keywords:
            await message.answer("No keywords set. Use /addkw <keyword> to add one.")
            return

        includes = [kw for kw in keywords if kw.is_include]
        excludes = [kw for kw in keywords if not kw.is_include]

        lines = ["<b>🔑 Your Keywords:</b>\n"]

        if includes:
            lines.append("<b>Include:</b>")
            for kw in includes:
                lines.append(f"  ✅ {kw.word}")

        if excludes:
            lines.append("\n<b>Exclude:</b>")
            for kw in excludes:
                lines.append(f"  ❌ {kw.word}")

        await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("clearkw"))
async def cmd_clear_keywords(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        stmt = select(Keyword).where(Keyword.user_id == user.id)
        result = await session.execute(stmt)
        keywords = list(result.scalars().all())

        if not keywords:
            await message.answer("No keywords to clear.")
            return

        for kw in keywords:
            await session.delete(kw)
        await session.commit()
        await message.answer(f"✅ Cleared {len(keywords)} keywords.")
