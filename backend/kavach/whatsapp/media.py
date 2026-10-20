"""Download WhatsApp media to short-lived local storage."""

from pathlib import Path
import mimetypes
import uuid

import httpx

from kavach.config import settings


async def download_media(media_id: str, filename: str | None = None) -> Path:
    if not settings.wa_token:
        raise RuntimeError("WA_TOKEN must be configured to download media")

    headers = {"Authorization": f"Bearer {settings.wa_token}"}
    media_info_url = (
        f"https://graph.facebook.com/{settings.graph_version}/{media_id}"
    )

    async with httpx.AsyncClient(timeout=30) as client:
        info_response = await client.get(media_info_url, headers=headers)
        info_response.raise_for_status()
        media_url = info_response.json().get("url")

        if not media_url:
            raise RuntimeError("Meta did not return a media download URL")

        file_response = await client.get(media_url, headers=headers)
        file_response.raise_for_status()

    content_type = file_response.headers.get("content-type", "")
    suffix = Path(filename or "").suffix or mimetypes.guess_extension(
        content_type.split(";", 1)[0]
    ) or ".bin"

    settings.files_dir.mkdir(parents=True, exist_ok=True)
    destination = settings.files_dir / f"{uuid.uuid4().hex}{suffix}"
    destination.write_bytes(file_response.content)
    return destination