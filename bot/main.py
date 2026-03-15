import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import BotCommand, Message

from bot.config import settings
from bot.database import init_db
from bot.handlers import feeds, groups, keywords, opml, digest
from bot.services.scheduler_service import setup_scheduler, shutdown_scheduler

main_router = Router()


HELP_TEXT = (
    "<b>📡 RSS Aggregator Bot</b>\n\n"
    "<b>Feed Management:</b>\n"
    "/add &lt;url&gt; — Add a new RSS feed\n"
    "/remove &lt;id&gt; — Remove a feed\n"
    "/list — List all feeds\n"
    "/toggle &lt;id&gt; — Pause/resume a feed\n"
    "/check — Check all feeds now\n\n"
    "<b>Groups:</b>\n"
    "/newgroup &lt;name&gt; — Create a feed group\n"
    "/groups — List all groups\n"
    "/addtogroup &lt;group_id&gt; &lt;feed_id&gt; — Add feed to group\n"
    "/rmfromgroup &lt;group_id&gt; &lt;feed_id&gt; — Remove feed from group\n"
    "/delgroup &lt;id&gt; — Delete a group\n\n"
    "<b>Keywords:</b>\n"
    "/addkw &lt;word&gt; — Add include keyword\n"
    "/addkw -&lt;word&gt; — Add exclude keyword\n"
    "/rmkw &lt;word&gt; — Remove a keyword\n"
    "/keywords — List keywords\n"
    "/clearkw — Clear all keywords\n\n"
    "<b>Digest:</b>\n"
    "/digest — Toggle digest mode\n"
    "/digesttime &lt;hour&gt; [min] — Set digest time (UTC)\n"
    "/digeststatus — View digest settings\n\n"
    "<b>Import/Export:</b>\n"
    "/import — Import feeds from OPML\n"
    "/export — Export feeds to OPML\n\n"
    "<b>Other:</b>\n"
    "/help — Show this help message"
)


@main_router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Welcome to <b>RSS Aggregator Bot</b>!\n\n"
        "I can help you track RSS feeds and deliver updates right here in Telegram.\n\n"
        "Use /help to see all available commands.",
        parse_mode="HTML",
    )


@main_router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode="HTML")


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show help message"),
        BotCommand(command="add", description="Add RSS feed"),
        BotCommand(command="remove", description="Remove a feed"),
        BotCommand(command="list", description="List all feeds"),
        BotCommand(command="toggle", description="Toggle feed active/paused"),
        BotCommand(command="check", description="Check feeds now"),
        BotCommand(command="newgroup", description="Create a feed group"),
        BotCommand(command="groups", description="List groups"),
        BotCommand(command="addkw", description="Add keyword filter"),
        BotCommand(command="keywords", description="List keywords"),
        BotCommand(command="digest", description="Toggle digest mode"),
        BotCommand(command="export", description="Export feeds as OPML"),
    ]
    await bot.set_my_commands(commands)


async def on_startup(bot: Bot):
    await init_db()
    setup_scheduler(bot)
    await set_bot_commands(bot)


async def on_shutdown(bot: Bot):
    shutdown_scheduler()


async def main():
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.include_router(main_router)
    dp.include_router(feeds.router)
    dp.include_router(groups.router)
    dp.include_router(keywords.router)
    dp.include_router(opml.router)
    dp.include_router(digest.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
