# ────────────────────────────────────────────────────────────────
#
# Google Drive backups for Mariya File Share.
# Creates a local ZIP in ./backup and uploads it to a private Drive folder.
# Secrets and environment variables are deliberately excluded.
#
# ────────────────────────────────────────────────────────────────

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import aiohttp
from bson import json_util
from pyrogram import filters
from pyrogram.types import Message

from bot import Bot
from config import (
    GDRIVE_CLIENT_ID,
    GDRIVE_CLIENT_SECRET,
    GDRIVE_REFRESH_TOKEN,
    GDRIVE_FOLDER_ID,
)
from database.database import database
from helper_func import admin_filter

_DRIVE_API = "https://www.googleapis.com/drive/v3"
_DRIVE_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_FOLDER_NAME = "Mariya Backups"
_backup_lock = asyncio.Lock()


def _configured() -> bool:
    return bool(GDRIVE_CLIENT_ID and GDRIVE_CLIENT_SECRET and GDRIVE_REFRESH_TOKEN)


async def _response_json(response, action: str):
    try:
        payload = await response.json(content_type=None)
    except Exception:
        payload = {"error": (await response.text())[:500]}
    if response.status >= 400:
        detail = payload.get("error_description") or payload.get("error", {}).get("message") or payload.get("error")
        raise RuntimeError(f"{action} failed (HTTP {response.status}): {detail}")
    return payload


async def _access_token(session: aiohttp.ClientSession) -> str:
    async with session.post(
        _TOKEN_URL,
        data={
            "client_id": GDRIVE_CLIENT_ID,
            "client_secret": GDRIVE_CLIENT_SECRET,
            "refresh_token": GDRIVE_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
    ) as response:
        data = await _response_json(response, "Google authorization")
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Google did not return an access token.")
    return token


async def _folder_id(session: aiohttp.ClientSession, headers: dict) -> str:
    if GDRIVE_FOLDER_ID:
        return GDRIVE_FOLDER_ID

    params = {
        "q": "name = 'Mariya Backups' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        "pageSize": "10",
        "fields": "files(id,name)",
    }
    async with session.get(f"{_DRIVE_API}/files", headers=headers, params=params) as response:
        data = await _response_json(response, "Drive folder lookup")
    folders = data.get("files") or []
    if folders:
        return folders[0]["id"]

    async with session.post(
        f"{_DRIVE_API}/files",
        headers={**headers, "Content-Type": "application/json"},
        json={"name": _FOLDER_NAME, "mimeType": "application/vnd.google-apps.folder"},
    ) as response:
        data = await _response_json(response, "Drive folder creation")
    return data["id"]


async def _upload_file(session: aiohttp.ClientSession, headers: dict, folder_id: str, path: Path):
    size = path.stat().st_size
    metadata = {"name": path.name, "mimeType": "application/zip", "parents": [folder_id]}
    start_headers = {
        **headers,
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": "application/zip",
        "X-Upload-Content-Length": str(size),
    }
    async with session.post(
        _DRIVE_UPLOAD,
        params={"uploadType": "resumable", "fields": "id,name,size,webViewLink"},
        headers=start_headers,
        json=metadata,
    ) as response:
        await _response_json(response, "Drive upload initialization")
        upload_url = response.headers.get("Location")
    if not upload_url:
        raise RuntimeError("Google Drive did not provide a resumable upload URL.")

    with path.open("rb") as archive:
        async with session.put(
            upload_url,
            data=archive,
            headers={"Content-Type": "application/zip", "Content-Length": str(size)},
        ) as response:
            return await _response_json(response, "Backup upload")


async def _create_archive() -> Path:
    folder = Path("backup")
    folder.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    filename = f"Mariya_backup_{now.strftime('%Y%m%d_%H%M%S_UTC')}.zip"
    archive_path = folder / filename

    collection_names = await database.list_collection_names()
    manifest = {
        "product": "Mariya File Share",
        "format_version": 1,
        "created_at_utc": now.isoformat(),
        "database": database.name,
        "collections": [],
        "notes": [
            "Environment variables, bot tokens, API hashes, OAuth secrets and database credentials are not included.",
            "Generated Telegram deep-link history is included from the generated_links collection.",
            "Original videos remain in the Telegram DB channel; this archive backs up database records and metadata, not video media.",
        ],
    }

    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for name in sorted(collection_names):
            if name.startswith("system."):
                continue
            documents = await database[name].find({}).to_list(length=None)
            archive.writestr(
                f"database/{name}.json",
                json_util.dumps(documents, indent=2, ensure_ascii=False),
            )
            manifest["collections"].append({"name": name, "documents": len(documents)})

        # Preserve any operator-created text exports placed in the backup folder.
        for text_file in folder.glob("*.txt"):
            if text_file.is_file():
                archive.write(text_file, arcname=f"generated_text/{text_file.name}")

        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

    return archive_path


@Bot.on_message(filters.private & filters.command("backup") & admin_filter)
async def create_backup(client: Bot, message: Message):
    if not _configured():
        return await message.reply_text(
            "⚙️ Google Drive backup isn't configured yet. Add GDRIVE_CLIENT_ID, "
            "GDRIVE_CLIENT_SECRET and GDRIVE_REFRESH_TOKEN to Render environment variables."
        )

    if _backup_lock.locked():
        return await message.reply_text("⏳ A backup is already running. Please wait for it to finish.")

    async with _backup_lock:
        status = await message.reply_text("📦 Creating Mariya's backup…")
        archive_path = None
        try:
            archive_path = await _create_archive()
            timeout = aiohttp.ClientTimeout(total=300, connect=30, sock_read=300)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                token = await _access_token(session)
                headers = {"Authorization": f"Bearer {token}"}
                folder_id = await _folder_id(session, headers)
                uploaded = await _upload_file(session, headers, folder_id, archive_path)

            size_mb = archive_path.stat().st_size / (1024 * 1024)
            link = uploaded.get("webViewLink")
            result = (
                "✅ <b>Backup uploaded to Google Drive.</b>\n\n"
                f"📦 <code>{archive_path.name}</code>\n"
                f"💾 Size: <b>{size_mb:.2f} MB</b>\n"
                f"🗂 Collections: <b>{len((await database.list_collection_names()))}</b>"
            )
            if link:
                result += f"\n\n<a href=\"{link}\">Open backup in Drive</a>"
            await status.edit_text(result, disable_web_page_preview=True)
        except Exception as error:
            await status.edit_text(
                "❌ <b>Backup failed.</b>\n\n"
                f"<code>{str(error)[:900]}</code>\n\n"
                "The local ZIP, if created, remains in the Render backup folder for this running instance."
            )
        finally:
            # Keep the local ZIP as a short-lived convenience; Render's filesystem is ephemeral.
            pass

# ────────────────────────────────────────────────────────────────
