"""WhatsApp message clients for Meta Cloud API and Twilio Sandbox."""

import asyncio
import mimetypes
import re
from pathlib import Path

import httpx
from twilio.rest import Client as TwilioClient

from kavach.config import settings
import uuid
from urllib.parse import quote



def _uses_twilio() -> bool:
    return settings.whatsapp_provider == "twilio"


def _whatsapp_address(number: str) -> str:
    number = number.strip()
    if number.startswith("whatsapp:"):
        return number

    digits = re.sub(r"\D", "", number)
    if not digits:
        raise ValueError("WhatsApp phone number is empty or invalid")

    return f"whatsapp:+{digits}"


def _twilio_send_sync(to: str, body: str) -> dict:
    if settings.dry_run:
        print(f"[WHATSAPP DRY RUN] Twilio text to={to} body={body[:160]}")
        return {"dry_run": True}

    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        raise RuntimeError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are required")
    if not settings.twilio_whatsapp_from:
        raise RuntimeError("TWILIO_WHATSAPP_FROM is required")

    client = TwilioClient(
        settings.twilio_account_sid,
        settings.twilio_auth_token,
    )

    try:
        message = client.messages.create(
            from_=_whatsapp_address(settings.twilio_whatsapp_from),
            to=_whatsapp_address(to),
            body=body[:1600],
        )
    except Exception as exc:
        print(f"[TWILIO SEND ERROR] {type(exc).__name__}: {exc}")
        raise

    print(f"[TWILIO SEND] sid={message.sid} status={message.status}")
    return {"sid": message.sid, "status": message.status}

def _uses_telegram() -> bool:
    return settings.whatsapp_provider.strip().lower() == "telegram"

async def _download_telegram_media(
    file_id: str,
    filename: str | None = None,
) -> Path:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    async with httpx.AsyncClient(timeout=30) as client:
        info_response = await client.get(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/getFile",
            params={"file_id": file_id},
        )
        info_response.raise_for_status()
        info = info_response.json()

        if not info.get("ok"):
            raise RuntimeError("Telegram could not locate the requested file")

        remote_path = info.get("result", {}).get("file_path")
        if not remote_path:
            raise RuntimeError("Telegram did not return a file path")

        file_url = (
            "https://api.telegram.org/file/bot"
            f"{settings.telegram_bot_token}/{quote(remote_path, safe='/')}"
        )
        file_response = await client.get(file_url)
        file_response.raise_for_status()
        contents = file_response.content

    if len(contents) > 20 * 1024 * 1024:
        raise ValueError("Telegram files larger than 20 MB are not supported")

    settings.files_dir.mkdir(parents=True, exist_ok=True)

    source_name = Path(filename or remote_path).name
    suffix = Path(source_name).suffix.lower() or ".bin"
    destination = settings.files_dir / f"telegram-{uuid.uuid4().hex}{suffix}"
    destination.write_bytes(contents)

    return destination


async def _telegram_post(method: str, payload: dict) -> dict:
    if settings.dry_run:
        print(f"[TELEGRAM DRY RUN] {method} chat_id={payload.get('chat_id')}")
        return {"dry_run": True}

    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    url = (
        f"https://api.telegram.org/bot"
        f"{settings.telegram_bot_token}/{method}"
    )

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, json=payload)

    response.raise_for_status()
    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(result.get("description", "Telegram request failed"))

    return result["result"]


async def _telegram_upload(
    method: str,
    media_field: str,
    to: str,
    file_path: Path,
    filename: str,
) -> dict:
    if settings.dry_run:
        print(f"[TELEGRAM DRY RUN] {method} chat_id={to} path={file_path}")
        return {"dry_run": True}

    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"

    async with httpx.AsyncClient(timeout=30) as client:
        with file_path.open("rb") as file_handle:
            response = await client.post(
                url,
                data={"chat_id": to},
                files={media_field: (filename, file_handle, mime_type)},
            )

    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(result.get("description", "Telegram media upload failed"))
    return result["result"]


async def _send_twilio_text(to: str, body: str) -> dict:
    return await asyncio.to_thread(_twilio_send_sync, to, body)


def _messages_url() -> str:
    return (
        f"https://graph.facebook.com/{settings.graph_version}/"
        f"{settings.wa_phone_id}/messages"
    )


def _media_url() -> str:
    return (
        f"https://graph.facebook.com/{settings.graph_version}/"
        f"{settings.wa_phone_id}/media"
    )


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.wa_token}"}


async def _post_meta_message(payload: dict) -> dict:
    if settings.dry_run:
        print("[WHATSAPP DRY RUN]", payload)
        return {"dry_run": True}

    if not settings.wa_token or not settings.wa_phone_id:
        raise RuntimeError("WA_TOKEN and WA_PHONE_ID must be configured")

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            _messages_url(),
            headers=_headers(),
            json={"messaging_product": "whatsapp", **payload},
        )

    response.raise_for_status()
    return response.json()


async def send_text(to: str, body: str) -> dict:
    if _uses_telegram():
        return await _telegram_post(
            "sendMessage",
            {"chat_id": to, "text": body[:4000]},
        )


    if _uses_twilio():
        return await _send_twilio_text(to, body)
    return await _post_meta_message({
        "to": to,
        "type": "text",
        "text": {"body": body[:4000]},
    })


async def send_buttons(
    to: str,
    body: str,
    buttons: list[tuple[str, str]],
) -> dict:
    if _uses_telegram():
        return await _telegram_post(
            "sendMessage",
            {
                "chat_id": to,
                "text": body[:4000],
                "reply_markup": {
                    "keyboard": [
                        [{"text": title[:64]} for _, title in buttons[:3]]
                    ],
                    "resize_keyboard": True,
                    "one_time_keyboard": True,
                },
            },
        )
    if _uses_twilio():
        # Twilio Sandbox uses typed replies here; the webhook maps known labels
        # back to Kavach's button IDs.
        options = "\n".join(f"• {title}" for _, title in buttons[:3])
        return await _send_twilio_text(to, f"{body}\n\n{options}")

    button_items = [
        {
            "type": "reply",
            "reply": {"id": button_id[:256], "title": title[:20]},
        }
        for button_id, title in buttons[:3]
    ]

    return await _post_meta_message({
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body[:1024]},
            "action": {"buttons": button_items},
        },
    })


async def send_audio(to: str, path: str | Path) -> dict:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(file_path)

    if _uses_telegram():
        return await _telegram_upload(
            "sendAudio",
            "audio",
            to,
            file_path,
            file_path.name,
        )

    if _uses_twilio():
        # Twilio needs a public HTTPS media URL; this text-first adapter
        # doesn't publish local audio files yet.
        print(f"[TWILIO] Audio attachment not sent: {file_path}")
        return {"media_skipped": True}

    mime_type = mimetypes.guess_type(file_path.name)[0] or "audio/mpeg"
    if not mime_type.startswith("audio/"):
        raise ValueError(f"Expected an audio file, got {mime_type}")

    if settings.dry_run:
        print(f"[WHATSAPP DRY RUN] audio to={to} path={file_path}")
        return {"dry_run": True}

    if not settings.wa_token or not settings.wa_phone_id:
        raise RuntimeError("WA_TOKEN and WA_PHONE_ID must be configured")

    async with httpx.AsyncClient(timeout=30) as client:
        with file_path.open("rb") as file_handle:
            upload = await client.post(
                _media_url(),
                headers=_headers(),
                data={
                    "messaging_product": "whatsapp",
                    "type": mime_type,
                },
                files={"file": (file_path.name, file_handle, mime_type)},
            )

        upload.raise_for_status()
        media_id = upload.json()["id"]

    return await _post_meta_message({
        "to": to,
        "type": "audio",
        "audio": {"id": media_id},
    })


async def send_document(to: str, path: str | Path, filename: str) -> dict:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(file_path)

    if _uses_telegram():
        return await _telegram_upload(
            "sendDocument",
            "document",
            to,
            file_path,
            filename,
        )

    if _uses_twilio():
        # Twilio needs a public HTTPS media URL to deliver local PDFs.
        return await _send_twilio_text(
            to,
            f"Kavach created {filename}, but PDF attachment delivery "
            "is not enabled in this Twilio demo yet.",
        )

    if settings.dry_run:
        print(f"[WHATSAPP DRY RUN] document to={to} path={file_path}")
        return {"dry_run": True}

    if not settings.wa_token or not settings.wa_phone_id:
        raise RuntimeError("WA_TOKEN and WA_PHONE_ID must be configured")

    mime_type = mimetypes.guess_type(filename)[0] or "application/pdf"

    async with httpx.AsyncClient(timeout=30) as client:
        with file_path.open("rb") as file_handle:
            upload = await client.post(
                _media_url(),
                headers=_headers(),
                data={
                    "messaging_product": "whatsapp",
                    "type": mime_type,
                },
                files={"file": (filename, file_handle, mime_type)},
            )
        upload.raise_for_status()
        media_id = upload.json()["id"]

    return await _post_meta_message({
        "to": to,
        "type": "document",
        "document": {"id": media_id, "filename": filename},
    })