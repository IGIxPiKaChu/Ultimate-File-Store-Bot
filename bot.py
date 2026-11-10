#(©)CodeXBotz

import sys
from datetime import datetime
from aiohttp import web
import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode

from plugins import web_server
from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, FORCE_SUB_CHANNEL, CHANNEL_ID, PORT

ascii_art = """
░█████╗░░█████╗░██████╗░███████╗██╗░░██╗██████╗░░█████╗░████████╗███████╗
██╔══██╗██╔══██╗██╔══██╗╚════██║
██║░░╚═╝██║░░██║██║░░██║█████╗░░░╚███╔╝░██████╦╝
██║░░██╗██║░░██║██║░░██║██╔══╝░░░██╔██╗░
╚█████╔╝╚█████╔╝██████╔╝███████╗██╔╝╚██╗
░╚════╝░░╚════╝░╚═════╝░╚══════╝╚═╝░░╚═╝
"""

class Bot(Client):
    def __init__(self):
        if not TG_BOT_TOKEN or not APP_ID or not API_HASH:
            raise RuntimeError("Missing Telegram credentials: TG_BOT_TOKEN, APP_ID, or API_HASH.")
        if not CHANNEL_ID or not OWNER_ID:
            raise RuntimeError("Missing CHANNEL_ID or OWNER_ID.")
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        if FORCE_SUB_CHANNEL:
            try:
                link = (await self.get_chat(FORCE_SUB_CHANNEL)).invite_link
                if not link:
                    await self.export_chat_invite_link(FORCE_SUB_CHANNEL)
                    link = (await self.get_chat(FORCE_SUB_CHANNEL)).invite_link
                self.invitelink = link
            except Exception:
                self.LOGGER(__name__).exception("Force-sub channel setup failed. Check FORCE_SUB_CHANNEL and invite-link permission.")
                sys.exit(1)

        try:
            # A bot may not have a private channel's access hash cached after a fresh deploy.
            # Enumerating dialogs refreshes Pyrogram's peer storage before resolving by ID.
            db_channel = None
            async for dialog in self.get_dialogs():
                if dialog.chat.id == CHANNEL_ID:
                    db_channel = dialog.chat
                    break
            if db_channel is None:
                db_channel = await self.get_chat(CHANNEL_ID)

            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Mariya storage connection test")
            await test.delete()
        except Exception:
            self.LOGGER(__name__).exception(
                "DB channel connection failed. Confirm CHANNEL_ID is correct and that this bot account "
                "is a channel administrator. For a private channel, post one fresh message after adding "
                "the bot, then restart the service so Pyrogram can learn the channel peer."
            )
            sys.exit(1)

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info("Mariya bot connected successfully and is running.")
        print(ascii_art)
        print("Welcome to Mariya File Sharing Bot")
        self.username = usr_bot_me.username

        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Mariya stopped.")
