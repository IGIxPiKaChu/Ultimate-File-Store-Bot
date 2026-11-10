#(©)Mariya

import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import Bot
from config import ADMINS
from helper_func import encode, get_message_id


def _share_markup(link: str):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔁 Share URL", url=f"https://telegram.me/share/url?url={link}")
    ]])


# ORIGINAL MANUAL RANGE SYSTEM — /batch asks for first and last DB-channel posts.
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("batch"))
async def manual_batch(client: Bot, message: Message):
    if not getattr(client, "db_channel", None):
        await message.reply_text("Storage channel is not initialized. Post a new message in your configured storage channel first.")
        return

    while True:
        try:
            first_message = await client.ask(
                text="Forward the FIRST message from your DB channel (with quote), or send its DB channel post link.",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except Exception:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        await first_message.reply("❌ That message/link is not from my DB channel. Try again.", quote=True)

    while True:
        try:
            second_message = await client.ask(
                text="Forward the LAST message from your DB channel (with quote), or send its DB channel post link.",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except Exception:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        await second_message.reply("❌ That message/link is not from my DB channel. Try again.", quote=True)

    payload = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    encoded = await encode(payload)
    link = f"https://t.me/{client.username}?start={encoded}"
    await second_message.reply_text(
        f"<b>Here is your link</b>\n\n{link}",
        quote=True,
        reply_markup=_share_markup(link)
    )


# NEW AUTOMATIC UPLOAD SYSTEM — /upload batch ... /complete
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("help"))
async def help_command(client: Bot, message: Message):
    await message.reply_text(
        "<b>Mariya File Share — Help</b>\n\n"
        "OLD MANUAL SYSTEM:\n"
        "• Send /batch, then forward the first and last DB-channel messages.\n"
        "• Send /genlink, then forward one DB-channel message.\n\n"
        "NEW AUTOMATIC SYSTEM:\n"
        "• Send /upload batch, forward videos/files, then send /complete.\n"
        "• Send /cancel to cancel the active upload session."
    )


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("upload"))
async def upload_batch(client: Bot, message: Message):
    if len(message.command) < 2 or message.command[1].lower() != "batch":
        await message.reply_text("Use /upload batch to start an automatic batch upload.")
        return

    if not getattr(client, "db_channel", None):
        await message.reply_text(
            "Storage channel is not initialized yet. Post a new message in your configured private storage channel first."
        )
        return

    sessions = getattr(client, "upload_sessions", None)
    if sessions is None:
        client.upload_sessions = {}
        sessions = client.upload_sessions

    if message.from_user.id in sessions:
        await message.reply_text("A batch is already active. Forward your files, then send /complete. Use /cancel to discard the session.")
        return

    sessions[message.from_user.id] = {
        "first_id": None,
        "last_id": None,
        "count": 0,
        "lock": asyncio.Lock()
    }
    await message.reply_text(
        "💗 <b>Batch upload started.</b>\n\n"
        "Forward videos/files from any channel to Mariya. I'll save each one to the private storage channel.\n\n"
        "When finished, send /complete to receive one link for the whole batch.\n"
        "Send /cancel to cancel the batch session."
    )


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command(["stop", "complete"]))
async def stop_batch(client: Bot, message: Message):
    sessions = getattr(client, "upload_sessions", {})
    session = sessions.get(message.from_user.id)
    if session is None:
        await message.reply_text("There is no active automatic batch. Send /upload batch to start one.")
        return

    await asyncio.sleep(0.5)
    async with session["lock"]:
        if sessions.get(message.from_user.id) is session:
            sessions.pop(message.from_user.id, None)
        count = session["count"]
        first_id = session["first_id"]
        last_id = session["last_id"]

    if not count or first_id is None or last_id is None:
        await message.reply_text("The batch is empty, so I didn't create a link. Send /upload batch to try again.")
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
        await message.reply_text("There is no active automatic batch.")
    else:
        await message.reply_text(
            f"Automatic batch session cancelled. {session['count']} file(s) already saved remain in the storage channel, but no batch link was created."
        )


# ORIGINAL MANUAL SINGLE-FILE LINK SYSTEM — /genlink asks for one DB-channel post.
@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("genlink"))
async def link_generator(client: Bot, message: Message):
    if not getattr(client, "db_channel", None):
        await message.reply_text("Storage channel is not initialized. Post a new message in your configured storage channel first.")
        return

    while True:
        try:
            channel_message = await client.ask(
                text="Forward a message from the DB channel (with quote), or send its DB channel post link.",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except Exception:
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        await channel_message.reply("❌ That message/link is not from my DB channel. Try again.", quote=True)

    encoded = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={encoded}"
    await channel_message.reply_text(
        f"<b>Here is your link</b>\n\n{link}",
        quote=True,
        reply_markup=_share_markup(link)
    )
