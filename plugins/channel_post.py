#(©)CodeXBotz

import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from bot import Bot
from config import OWNER_ID, DISABLE_CHANNEL_BUTTON, CHANNEL_ID
from helper_func import encode


async def _copy_to_storage(client: Client, message: Message):
    try:
        return await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await message.copy(chat_id=client.db_channel.id, disable_notification=True)


def _share_markup(link: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔁 Share URL", url=f"https://telegram.me/share/url?url={link}")
    ]])


@Bot.on_message(
    filters.private & filters.user(OWNER_ID)
    & ~filters.command(["start", "users", "broadcast", "batch", "genlink", "stats", "stop", "cancel"])
)
async def channel_post(client: Client, message: Message):
    if not getattr(client, "db_channel", None):
        await message.reply_text(
            "Storage channel is not initialized. Post one new message in "
            "your configured private storage channel, then try again."
        )
        return

    sessions = getattr(client, "upload_sessions", {})
    session = sessions.get(message.from_user.id)

    if session is not None:
        if not message.media:
            await message.reply_text(
                "Please forward a video or file. Send /stop when you have finished the batch."
            )
            return

        status = await message.reply_text("Saving to Mariya storage…")
        try:
            async with session["lock"]:
                saved = await _copy_to_storage(client, message)
                if session["first_id"] is None:
                    session["first_id"] = saved.id
                session["last_id"] = saved.id
                session["count"] += 1
                count = session["count"]
        except Exception as e:
            client.LOGGER(__name__).exception("Batch file copy failed: %s", e)
            await status.edit_text("This file could not be saved. You can retry it.")
            return

        await status.edit_text(
            f"Added to batch: <b>{count}</b> file(s).\n"
            "Forward the next file or send /stop to get one link."
        )
        return

    status = await message.reply_text("Please wait…", quote=True)
    try:
        saved = await _copy_to_storage(client, message)
    except Exception as e:
        client.LOGGER(__name__).exception("File copy failed: %s", e)
        await status.edit_text("Something went wrong while saving this file.")
        return

    encoded = await encode(f"get-{saved.id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={encoded}"
    markup = _share_markup(link)
    await status.edit_text(
        f"<b>Here is your link</b>\n\n{link}",
        reply_markup=markup,
        disable_web_page_preview=True
    )

    if not DISABLE_CHANNEL_BUTTON:
        try:
            await saved.edit_reply_markup(markup)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await saved.edit_reply_markup(markup)
        except Exception:
            pass


@Bot.on_message(filters.channel & filters.incoming & filters.chat(CHANNEL_ID))
async def new_post(client: Client, message: Message):
    # Learn the private storage channel peer from its incoming channel update.
    client.db_channel = message.chat
    if DISABLE_CHANNEL_BUTTON:
        return

    encoded = await encode(f"get-{message.id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={encoded}"
    try:
        await message.edit_reply_markup(_share_markup(link))
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.edit_reply_markup(_share_markup(link))
    except Exception:
        pass
