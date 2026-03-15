from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.database import async_session
from bot.services.feed_service import get_or_create_user

router = Router()


@router.message(Command("digest"))
async def cmd_toggle_digest(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        user.digest_enabled = not user.digest_enabled
        await session.commit()

        if user.digest_enabled:
            await message.answer(
                f"✅ Digest mode <b>enabled</b>.\n"
                f"You'll receive a daily digest at {user.digest_hour:02d}:{user.digest_minute:02d} UTC.\n"
                f"Use /digesttime <hour> to change the time.",
                parse_mode="HTML",
            )
        else:
            await message.answer(
                "✅ Digest mode <b>disabled</b>.\nYou'll receive updates in real-time.",
                parse_mode="HTML",
            )


@router.message(Command("digesttime"))
async def cmd_digest_time(message: Message, command: CommandObject):
    if not command.args:
        await message.answer("Usage: /digesttime <hour> [minute]\nExample: /digesttime 9 or /digesttime 14 30")
        return

    parts = command.args.strip().split()
    try:
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        await message.answer("Hour and minute must be numbers.")
        return

    if not (0 <= hour <= 23) or not (0 <= minute <= 59):
        await message.answer("Hour must be 0-23, minute must be 0-59.")
        return

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        user.digest_hour = hour
        user.digest_minute = minute
        if not user.digest_enabled:
            user.digest_enabled = True
        await session.commit()

        await message.answer(
            f"✅ Digest time set to <b>{hour:02d}:{minute:02d} UTC</b>.\nDigest mode is now enabled.",
            parse_mode="HTML",
        )


@router.message(Command("digeststatus"))
async def cmd_digest_status(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        status = "enabled" if user.digest_enabled else "disabled"
        lines = [
            f"<b>📰 Digest Status</b>\n",
            f"Mode: <b>{status}</b>",
            f"Time: <b>{user.digest_hour:02d}:{user.digest_minute:02d} UTC</b>",
        ]
        await message.answer("\n".join(lines), parse_mode="HTML")
