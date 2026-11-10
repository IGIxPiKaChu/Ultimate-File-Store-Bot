#(©)Mariya

import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import Bot
from config import ADMINS
from helper_func import encode


def _share_markup(link: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔁 Share URL", url=f"https://telegram.me/share/url?url={link}")
    ]])


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("batch"))
async def batch(client: Bot, message: Message):
    if not getattr(client, "db_channel", None):
        await message.reply_text(
            "Storage channel is not initialized yet. Post a new message in "
            "your configured private storage channel first."
        )
        return

    sessions = getattr(client, "upload_sessions", None)
    if sessions is None:
        client.upload_sessions = {}
        sessions = client.upload_sessions

    if message.from_user.id in sessions:
        await message.reply_text(
            "A batch is already active. Forward your files, then send /stop. "
            "Use /cancel to discard the session."
        )
        return

    sessions[message.from_user.id] = {
        "first_id": None,
        "last_id": None,
        "count": 0,
        "lock": asyncio.Lock()
    }
    await message.reply_text(
        "💗 <b>Batch upload started.</b>\n\n"
        "Now forward videos/files from any channel to Mariya. "
        "I'll save each one to the private storage channel.\n\n"
        "When finished, send /stop to receive one link for the whole batch.\n"
        "Send /cancel to discard the batch session."
    )


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("stop"))
async def stop_batch(client: Bot, message: Message):
    sessions = getattr(client, "upload_sessions", {})
    session = sessions.get(message.from_user.id)
    if session is None:
        await message.reply_text("There is no active batch. Send /batch to start one.")
        return

    # Let earlier forwarded-message updates enter their handlers, then wait
    # for any active storage copy before closing the session.
    await asyncio.sleep(0.5)
    async with session["lock"]:
        if sessions.get(message.from_user.id) is session:
            sessions.pop(message.from_user.id, None)
        count = session["count"]
        first_id = session["first_id"]
        last_id = session["last_id"]

    if not count or first_id is None or last_id is None:
        await message.reply_text(
            "The batch is empty, so I didn't create a link. Send /batch to try again."
        )
        return

    channel_id = abs(client.db_channel.id)
    if first_id == last_id:
        payload = f"get-{first_id * channel_id}"
    else:
        payload = f"get-{first_id * channel_id}-{last_id * channel_id}"

    encoded = await encode(payload)
    link = f"https://t.me/{client.username}?start={encoded}"
    await message.reply_text(
        f"💗 <b>Batch completed!</b>\n"
        f"Files saved: <b>{count}</b>\n\n"
        f"<b>Your single batch link:</b>\n{link}",
        reply_markup=_share_markup(link),
        disable_web_page_preview=True
    )


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("cancel"))
async def cancel_batch(client: Bot, message: Message):
    sessions = getattr(client, "upload_sessions", {})
    session = sessions.pop(message.from_user.id, None)
    if session is None:
        await message.reply_text("There is no active batch.")
    else:
        await message.reply_text(
            f"Batch session cancelled. {session['count']} file(s) already saved "
            "remain in the storage channel, but no batch link was created."
        )


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("genlink"))
async def link_generator(client: Bot, message: Message):
    await message.reply_text(
        "For multiple files: send /batch, forward your files, then send /stop. "
        "For one file: just forward it to me."
    )
