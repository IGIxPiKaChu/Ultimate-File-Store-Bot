#(©)CodeXBotz

import os
import logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

load_dotenv()

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
APP_ID = int(os.environ.get("APP_ID", "0") or "0")
API_HASH = os.environ.get("API_HASH", "")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0") or "0")
OWNER_ID = int(os.environ.get("OWNER_ID", "0") or "0")
PORT = int(os.environ.get("PORT", "8080") or "8080")

DB_URI = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL", "")
DB_NAME = os.environ.get("DATABASE_NAME") or os.environ.get("DB_NAME", "filesharexbot")

FORCE_SUB_CHANNEL = int(os.environ.get("FORCE_SUB_CHANNEL", "0") or "0")
JOIN_REQUEST_ENABLE = os.environ.get("JOIN_REQUEST_ENABLED", os.environ.get("JOIN_REQUEST_ENABLE", "False")).lower() == "true"
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

START_PIC = os.environ.get("START_PIC", "")
START_MSG = os.environ.get("START_MESSAGE", "Hello {first}! 👋\\n\\nI’m Mariya, your personal file-sharing bot. Send me a file and I’ll create a private share link for you.")

FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "Hello {first}\\n\\n<b>You need to join in my Channel/Group to use me\\n\\nKindly Please join Channel</b>")
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)
PROTECT_CONTENT = os.environ.get("PROTECT_CONTENT", "False").lower() == "true"
AUTO_DELETE_TIME = int(os.getenv("AUTO_DELETE_TIME", os.getenv("TIME", "0")) or "0")
AUTO_DELETE_MSG = os.environ.get("AUTO_DELETE_MSG", "This file will be automatically deleted in {time} seconds. Please ensure you have saved any necessary content before this time.")
AUTO_DEL_SUCCESS_MSG = os.environ.get("AUTO_DEL_SUCCESS_MSG", "Your file has been successfully deleted. Thank you for using our service. ✅")
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", "False").lower() == "true"

BOT_STATS_TEXT = os.environ.get("BOT_STATS_TEXT", "<b>MARIYA UPTIME</b>\\n{uptime}")
USER_REPLY_TEXT = os.environ.get("USER_REPLY_TEXT", "💗 Welcome to Mariya. Only admins can upload files directly; everyone else can open a shared file link.")
ADMINS = [OWNER_ID] if OWNER_ID else []

LOG_FILE_NAME = "filesharingbot.txt"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[RotatingFileHandler(LOG_FILE_NAME, maxBytes=50000000, backupCount=10), logging.StreamHandler()]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
