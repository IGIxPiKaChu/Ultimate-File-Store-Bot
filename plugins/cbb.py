#(©)Mariya

from pyrogram import __version__
from bot import Bot
from config import OWNER_ID
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    if query.data == "about":
        await query.message.edit_text(
            text=f"<b>○ Creator : <a href='tg://user?id={OWNER_ID}'>Mariya Owner</a>\\n○ Language : <code>Python 3</code>\\n○ Library : <a href='https://docs.pyrogram.org/'>Pyrogram {__version__}</a>\\n○ Source Code : <a href='https://github.com/IGIxPiKaChu/Ultimate-File-Store-Bot'>Mariya File Store</a></b>",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔒 Close", callback_data="close")]])
        )
    elif query.data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except Exception:
            pass
