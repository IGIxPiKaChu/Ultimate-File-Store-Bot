# Mariya — Telegram File Sharing Bot

Mariya is a Telegram bot based on the open-source [CodeXBotz File-Sharing-Bot](https://github.com/CodeXBotz/File-Sharing-Bot).

It stores uploaded posts in a private Telegram database channel and creates shareable deep links. MongoDB stores user records; Telegram stores the actual media.

## Features
- Private-channel file storage and share links
- Single-file links and multi-file batch links
- Optional force-subscription gate
- Optional protected content
- Optional auto-delete for delivered files
- Owner-only upload and admin commands in this deployment
- MongoDB-backed user records
- Lightweight HTTP health endpoint for Render

## Required environment variables
- `TG_BOT_TOKEN` — bot token from BotFather
- `APP_ID` and `API_HASH` — Telegram API credentials
- `OWNER_ID` — your numeric Telegram user ID
- `CHANNEL_ID` — private database channel ID; add the bot as an administrator
- `DATABASE_URL` — MongoDB connection URI

Optional: `DATABASE_NAME`, `FORCE_SUB_CHANNEL`, `JOIN_REQUEST_ENABLED`, `START_MESSAGE`, `START_PIC`, `FORCE_SUB_MESSAGE`, `CUSTOM_CAPTION`, `DISABLE_CHANNEL_BUTTON`, `PROTECT_CONTENT`, `AUTO_DELETE_TIME`, `TG_BOT_WORKERS`, and `PORT`.

Legacy environment aliases `DB_URL`, `DB_NAME`, and `TIME` are also accepted.

## Run
```bash
pip install -r requirements.txt
python main.py
```

Render build command: `pip install -r requirements.txt`

Render start command: `python main.py`

## Important setup
1. Create a private Telegram channel for stored files.
2. Add Mariya as an administrator with permission to post and manage messages.
3. Set `CHANNEL_ID` to that channel's numeric ID.
4. Set `OWNER_ID` to your own Telegram numeric ID.
5. Add the MongoDB URI as `DATABASE_URL`.

Only `OWNER_ID` is authorized to upload directly. Do not add extra IDs to the `ADMINS` variable.

## Credits and license
This project is derived from [CodeXBotz/File-Sharing-Bot](https://github.com/CodeXBotz/File-Sharing-Bot). The upstream project is licensed under GNU GPL v3; the original license and copyright notices are retained in this repository. Changes for Mariya include branding, owner-only access, and environment compatibility.
