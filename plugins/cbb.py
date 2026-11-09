# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────

# 🔘 Start-menu buttons: About · Premium · Back · Close

from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import ADMINS

from bot import Bot
from core import ui


@Bot.on_callback_query(filters.regex(r"^(about|close|buy_prem|home)$"))
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    if data == "close":
        await query.answer()
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except Exception:
            pass
        return
    if data == "about":
        text, markup = ui.about_panel()
    elif data == "buy_prem":
        text, markup = ui.premium_panel(query.from_user)
    else:
        text, markup = ui.start_panel(query.from_user)
    await query.answer()
    await ui.edit_panel(client, query.message, text, markup)

# ────────────────────────────────────────────────────────────────

# ✅ THIS PROJECT IS DEVELOPED AND MAINTAINED BY @trinityXmods (TELEGRAM)
# 🚫 DO NOT REMOVE OR ALTER THIS CREDIT LINE UNDER ANY CIRCUMSTANCES.

# ⭐ FOR MORE HIGH-QUALITY OPEN-SOURCE BOTS, FOLLOW US ON GITHUB.
# 🔗 OFFICIAL GITHUB: https://github.com/Trinity-Mods
# 📩 NEED HELP OR HAVE QUESTIONS? REACH OUT VIA TELEGRAM: @the_universal_being

# ────────────────────────────────────────────────────────────────



@Bot.on_callback_query(filters.regex(r"^help:(upload|link|commands)$"))
async def help_menu_callback(client: Bot, query: CallbackQuery):
    section = query.data.split(":", 1)[1]
    is_admin = query.from_user and query.from_user.id in ADMINS
    if section == "upload":
        if is_admin:
            text = "<b>📤 Upload files to Mariya</b>\n\nSend a document, video, audio or other supported file directly to this chat. Mariya will store it in the private database channel. Then use <code>/genlink</code> on a stored post to create a share link."
        else:
            text = "<b>📤 File uploads</b>\n\nUploading is restricted to Mariya administrators. If you need to share a file, ask an administrator to create a link."
    elif section == "link":
        if is_admin:
            text = "<b>🔗 Generate a share link</b>\n\n• Reply to one stored channel post with <code>/genlink</code>.\n• Reply to the first post in a batch with <code>/batch</code>, then provide the last message ID when asked.\n\nOnly administrators can create links."
        else:
            text = "<b>🔗 Share links</b>\n\nOpen a link shared by a Mariya administrator to receive its file. Link creation is restricted to administrators."
    else:
        text = "<b>📚 Mariya help</b>\n\n/start — Open the main menu\n/help — Show this help\n/ping — Check bot response time\n/refer — Referral status (when enabled)\n\n<b>Admin commands</b>\n/genlink — Create a link for one stored post\n/batch — Create a link for a range of posts\n/settings — Configure access rules\n/stats — View uptime and usage\n/broadcast — Message registered users"
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="home"), InlineKeyboardButton("✖ Close", callback_data="close")]])
    await query.answer()
    await ui.edit_panel(client, query.message, text, markup)


@Bot.on_message(filters.command("help") & filters.private)
async def help_command(client: Bot, message: Message):
    text = "<b>📚 Mariya help</b>\n\n/start — Open the main menu\n/help — Show this help\n/ping — Check bot response time\n/refer — Referral status (when enabled)\n\n<b>Admin commands</b>\n/genlink — Create a link for one stored post\n/batch — Create a link for a range of posts\n/settings — Configure access rules\n/stats — View uptime and usage\n/broadcast — Message registered users"
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Main menu", callback_data="home")]])
    await message.reply_text(text, reply_markup=markup, disable_web_page_preview=True)
