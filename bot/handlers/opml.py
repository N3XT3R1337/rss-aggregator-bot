from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

from bot.database import async_session
from bot.services.feed_service import get_or_create_user
from bot.services.opml_service import export_opml, import_opml

router = Router()


@router.message(Command("export"))
async def cmd_export_opml(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        opml_content = await export_opml(session, user)

        if not opml_content.strip():
            await message.answer("No feeds to export.")
            return

        file = BufferedInputFile(
            opml_content.encode("utf-8"),
            filename="feeds.opml",
        )
        await message.answer_document(file, caption="📤 Your feeds exported as OPML.")


@router.message(Command("import"))
async def cmd_import_opml(message: Message):
    await message.answer(
        "📥 Send me an OPML file to import your feeds.\n"
        "Just upload the .opml or .xml file as a document."
    )


@router.message(F.document)
async def handle_opml_upload(message: Message):
    document = message.document
    if not document:
        return

    file_name = document.file_name or ""
    if not file_name.lower().endswith((".opml", ".xml")):
        await message.answer("Please send a .opml or .xml file.")
        return

    file = await message.bot.download(document)
    content = file.read().decode("utf-8")

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)

        try:
            added, skipped, groups = await import_opml(session, user, content)
            lines = [
                "✅ <b>OPML Import Complete</b>\n",
                f"📥 Feeds added: {added}",
                f"⏭️ Feeds skipped (duplicates): {skipped}",
                f"📁 Groups created: {groups}",
            ]
            await message.answer("\n".join(lines), parse_mode="HTML")
        except Exception:
            await message.answer("❌ Failed to parse OPML file. Please check the file format.")
