# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 🛡️ Admin tools: /users · /broadcast · /auth · /add_admin · /del_admin · /admins · /restart · /add_prem

import asyncio
import os
import sys
import time

from pyrogram import filters
from pyrogram.errors import FloodWait, InputUserDeactivated, ListenerTimeout, UserIsBlocked
from pyrogram.types import Message

from bot import Bot
from config import ADMINS, CONFIG_ADMINS, DB_CHANNELS, OWNER_ID, OWNER_TAG
from database.database import (
    add_admin, ban_user, del_admin, full_adminbase, full_userbase, is_banned, list_banned_users, mark_blocked,
    present_admin, referral_counts, save_storage_channel_ids, unban_user, user_counts,
)
from helper_func import PREMIUM_PLANS, admin_filter, increasepremtime

WAIT_MSG = """<b>Processing ...</b>"""

REPLY_ERROR = """<code>Use this command as a reply to any telegram message without any spaces.</code>"""


async def _ask_user_id(client, message: Message, prompt: str):
    """Use the ID given after the command, or ask for one. Returns None if cancelled / timed out."""
    if len(message.command) > 1 and message.command[1].lstrip("-").isdigit():
        return int(message.command[1])
    while True:
        try:
            answer = await client.ask(chat_id=message.from_user.id, text=prompt, timeout=60)
        except ListenerTimeout:
            await message.reply("⏳ ᴛɪᴍᴇ'ꜱ ᴜᴘ — ᴄᴏᴍᴍᴀɴᴅ ᴄᴀɴᴄᴇʟʟᴇᴅ.")
            return None
        text = (answer.text or "").strip()
        if text == "/cancel":
            await answer.reply("Cancelled 😉!")
            return None
        if text.lstrip("-").isdigit():
            return int(text)
        await answer.reply("❌ Error 😖\n\nThat's not a valid user ID — send numbers only.", quote=True)


@Bot.on_message(filters.command('users') & filters.private & admin_filter)
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    counts = await user_counts()
    refs = await referral_counts()
    await msg.edit(
        f"<b>👥 {counts['total']} users are using this bot</b>\n\n"
        f"🟢 ᴀᴄᴛɪᴠᴇ: <b>{counts['active']}</b>\n"
        f"🚫 ʙʟᴏᴄᴋᴇᴅ ᴛʜᴇ ʙᴏᴛ: <b>{counts['blocked']}</b>\n"
        f"🤝 ᴊᴏɪɴᴇᴅ ᴠɪᴀ ʀᴇꜰᴇʀʀᴀʟ: <b>{refs['confirmed']}</b>"
    )


@Bot.on_message(filters.private & filters.command('broadcast') & admin_filter)
async def send_text(client: Bot, message: Message):
    if not message.reply_to_message:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()
        return

    query = await full_userbase()
    broadcast_msg = message.reply_to_message
    total = successful = blocked = deleted = unsuccessful = 0
    pls_wait = await message.reply(f"<i>ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ ᴛᴏ {len(query)} ᴜꜱᴇʀꜱ.. ᴛʜɪꜱ ᴍᴀʏ ᴀɴᴅ ᴡɪʟʟ ᴛᴀᴋᴇ ꜱᴏᴍᴇ ᴛɪᴍᴇ ⌛</i>")
    last_update = time.monotonic()

    for chat_id in query:
        try:
            await broadcast_msg.copy(chat_id)
            successful += 1
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except Exception:
                unsuccessful += 1
        except UserIsBlocked:
            await mark_blocked(chat_id)
            blocked += 1
        except InputUserDeactivated:
            await mark_blocked(chat_id)
            deleted += 1
        except Exception:
            unsuccessful += 1
        total += 1
        if time.monotonic() - last_update > 15:
            last_update = time.monotonic()
            try:
                await pls_wait.edit(f"<i>ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ… {total}/{len(query)} ᴅᴏɴᴇ ⌛</i>")
            except Exception:
                pass
        await asyncio.sleep(0.04)

    status = f"""<b><u>Broadcast Completed 🟢</u>

ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ: <code>{total}</code>
ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: <code>{successful}</code>
ʙʟᴏᴄᴋᴇᴅ ᴜꜱᴇʀꜱ: <code>{blocked}</code>
ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛꜱ: <code>{deleted}</code>
ᴜɴꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: <code>{unsuccessful}</code></b>"""
    await pls_wait.edit(status)


@Bot.on_message(filters.command('auth') & filters.private)
async def auth_command(client: Bot, message: Message):
    await client.send_message(
        chat_id=OWNER_ID,
        text=f"Message for @{OWNER_TAG}\n<code>{message.from_user.id}</code>\n/add_admin <code>{message.from_user.id}</code> 🤫",
    )
    await message.reply("Please wait for verification from the owner. 🫣")


@Bot.on_message(filters.command('add_admin') & filters.private & filters.user(OWNER_ID))
async def command_add_admin(client: Bot, message: Message):
    admin_id = await _ask_user_id(client, message, "Enter admin id 🔢\n /cancel to cancel : ")
    if admin_id is None:
        return
    try:
        await client.get_users(admin_id)
    except Exception:
        return await message.reply("❌ Error 😖\n\nThe admin id is incorrect (or they haven't started the bot yet).", quote=True)
    if admin_id in ADMINS:
        return await message.reply("admin already exist. 💀")
    try:
        await add_admin(admin_id)
    except Exception:
        return await message.reply("Failed to add admin. 😔\nSome error occurred.")
    await message.reply(f"Added admin <code>{admin_id}</code> 😼")
    try:
        await client.send_message(chat_id=admin_id, text="You are verified, ask the owner to add them to db channels. 😁")
    except Exception:
        await message.reply("Failed to send invite. Please ensure that they have started the bot. 🥲")


@Bot.on_message(filters.command('del_admin') & filters.private & filters.user(OWNER_ID))
async def delete_admin_command(client: Bot, message: Message):
    admin_id = await _ask_user_id(client, message, "Enter admin id 🔢\n /cancel to cancel : ")
    if admin_id is None:
        return
    if admin_id == OWNER_ID or admin_id in CONFIG_ADMINS:
        return await message.reply("⚠️ This admin is set in the config (ADMINS / OWNER_ID) — remove them there instead.")
    if not await present_admin(admin_id):
        return await message.reply("admin doesn't exist. 💀")
    try:
        await del_admin(admin_id)
        await message.reply(f"Admin <code>{admin_id}</code> removed successfully 😀")
    except Exception:
        await message.reply("Failed to remove admin. 😔\nSome error occurred.")


@Bot.on_message(filters.command('admins') & filters.private & admin_filter)
async def admin_list_command(client: Bot, message: Message):
    db_admins = await full_adminbase()
    lines = [f"👑 <code>{OWNER_ID}</code> (owner)"]
    lines += [f"⚙️ <code>{a}</code> (config)" for a in CONFIG_ADMINS if a != OWNER_ID]
    lines += [f"➕ <code>{a}</code>" for a in db_admins if a != OWNER_ID and a not in CONFIG_ADMINS]
    await message.reply("<b>Full admin list 📃</b>\n\n" + "\n".join(lines))


def _target_user_id(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    if len(message.command) > 1 and message.command[1].lstrip("-").isdigit():
        user_id = int(message.command[1])
        return user_id if user_id > 0 else None
    return None


@Bot.on_message(filters.command("ban") & filters.private & admin_filter)
async def ban_command(client: Bot, message: Message):
    user_id = _target_user_id(message)
    if user_id is None:
        return await message.reply("Reply to a user or use <code>/ban USER_ID</code>.")
    if user_id == OWNER_ID or user_id in ADMINS:
        return await message.reply("Owner and administrators cannot be banned.")
    if await is_banned(user_id):
        return await message.reply(f"<code>{user_id}</code> is already banned.")
    await ban_user(user_id, message.from_user.id)
    await message.reply(f"Blocked <code>{user_id}</code> from using the bot.")


@Bot.on_message(filters.command("unban") & filters.private & admin_filter)
async def unban_command(client: Bot, message: Message):
    user_id = _target_user_id(message)
    if user_id is None:
        return await message.reply("Use <code>/unban USER_ID</code>.")
    if not await is_banned(user_id):
        return await message.reply(f"<code>{user_id}</code> is not banned.")
    await unban_user(user_id)
    await message.reply(f"Unblocked <code>{user_id}</code>.")


@Bot.on_message(filters.command("banned") & filters.private & admin_filter)
async def banned_users_command(client: Bot, message: Message):
    users = await list_banned_users()
    if not users:
        return await message.reply("There are no banned users.")
    lines = [f"<code>{user['_id']}</code>" for user in users]
    suffix = "\nShowing the latest 100." if len(users) == 100 else ""
    await message.reply("<b>Banned user IDs</b>\n" + "\n".join(lines) + suffix)


@Bot.on_message(filters.command("adddb") & filters.private & filters.user(OWNER_ID))
async def add_storage_channel(client: Bot, message: Message):
    if len(message.command) != 2 or not message.command[1].lstrip("-").isdigit():
        return await message.reply("Use <code>/adddb -100CHANNEL_ID</code>.")
    if int(message.command[1]) >= 0:
        return await message.reply("Storage channel IDs must be negative (for example, <code>-1001234567890</code>).")
    try:
        channel = await client.get_chat(int(message.command[1]))
        test = await client.send_message(channel.id, "Storage channel check")
        await test.delete()
    except Exception as error:
        return await message.reply(
            f"Could not validate that channel ({type(error).__name__}). Make the bot an admin and try again."
        )
    client.db_channels[channel.id] = channel
    await save_storage_channel_ids(list(client.db_channels))
    await message.reply(f"Added <b>{channel.title}</b> (<code>{channel.id}</code>) as a storage channel.")


@Bot.on_message(filters.command("removedb") & filters.private & filters.user(OWNER_ID))
async def remove_storage_channel(client: Bot, message: Message):
    if len(message.command) != 2 or not message.command[1].lstrip("-").isdigit():
        return await message.reply("Use <code>/removedb -100CHANNEL_ID</code>.")
    channel_id = int(message.command[1])
    if channel_id >= 0:
        return await message.reply("Storage channel IDs must be negative.")
    if channel_id == client.db_channel.id:
        return await message.reply("The primary storage channel cannot be removed.")
    if channel_id in DB_CHANNELS:
        return await message.reply("This channel is configured in DB_CHANNELS. Remove it there and restart the bot.")
    if channel_id not in client.db_channels:
        return await message.reply("That channel is not configured.")
    del client.db_channels[channel_id]
    await save_storage_channel_ids(list(client.db_channels))
    await message.reply(f"Removed <code>{channel_id}</code>. Existing links from that channel will stop working.")


@Bot.on_message(filters.command("dbchannels") & filters.private & admin_filter)
async def storage_channels_command(client: Bot, message: Message):
    lines = []
    for channel_id, channel in client.db_channels.items():
        marker = "primary" if channel_id == client.db_channel.id else "additional"
        lines.append(f"• {channel.title} — <code>{channel_id}</code> ({marker})")
    await message.reply("<b>Storage channels</b>\n" + "\n".join(lines))


@Bot.on_message(filters.private & filters.command('restart') & admin_filter)
async def restart(client: Bot, message: Message):
    msg = await message.reply_text(text="<i>ʀᴇꜱᴛᴀʀᴛɪɴɢ ᴛʜᴇ ꜱᴇʀᴠᴇʀꜱ 🔃</i>", quote=True)
    await asyncio.sleep(5)
    await msg.edit("<i>ꜱᴇʀᴠᴇʀꜱ ʀᴇꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅</i>")
    try:
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        print(e)


@Bot.on_message(filters.command('add_prem') & filters.private & admin_filter)
async def add_user_premium_command(client: Bot, message: Message):
    user_id = await _ask_user_id(client, message, "ᴇɴᴛᴇʀ ᴛʜᴇ ɪᴅ ᴏꜰ ᴜꜱᴇʀ 🔢\n\nᴘʀᴇꜱꜱ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ: ")
    if user_id is None:
        return
    plan = int(message.command[2]) if len(message.command) > 2 and message.command[2].isdigit() else None
    while plan not in PREMIUM_PLANS:
        try:
            answer = await client.ask(
                chat_id=message.from_user.id,
                text="Enter the amount of time you want to provide the premium \nChoose correctly. Its not reversible.\n\n"
                     "⁕ <code>1</code> for 7 days.\n⁕ <code>2</code> for 1 Month\n⁕ <code>3</code> for 3 Month\n"
                     "⁕ <code>4</code> for 6 Month\n⁕ <code>5</code> for 1 year.🤑",
                timeout=60,
            )
        except ListenerTimeout:
            return await message.reply("⏳ ᴛɪᴍᴇ'ꜱ ᴜᴘ — ᴄᴏᴍᴍᴀɴᴅ ᴄᴀɴᴄᴇʟʟᴇᴅ.")
        text = (answer.text or "").strip()
        if text == "/cancel":
            return await answer.reply("Cancelled 😉!")
        plan = int(text) if text.isdigit() else None
        if plan not in PREMIUM_PLANS:
            await message.reply("You have given wrong input. 😖")
    try:
        timestring, _ = await increasepremtime(user_id, plan)
        await message.reply("Premium added! 🤫")
        await client.send_message(
            chat_id=user_id,
            text=f"ᴀ ʟᴏᴠᴇʟʏ ᴜᴘᴅᴀᴛᴇ ꜰᴏʀ ʏᴏᴜ ʜᴇʀᴇ!\n\nᴀ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ ᴏꜰ {timestring} ʜᴀꜱ ʙᴇᴇɴ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ꜰᴏʀ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ! ✨",
        )
    except Exception as e:
        print(e)
        await message.reply("Some error occurred.\nCheck logs.. 😖\nIf you got premium added message then its ok.")

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────
