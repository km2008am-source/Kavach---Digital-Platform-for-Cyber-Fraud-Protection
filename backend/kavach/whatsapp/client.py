"""Meta WhatsApp Cloud API message client."""

from pathlib import Path
import mimetypes

import httpx

from kavach.config import settings


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


async def _post_message(payload: dict) -> dict:
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
    return await _post_message({
        "to": to,
        "type": "text",
        "text": {"body": body[:4000]},
    })


async def send_buttons(
    to: str,
    body: str,
    buttons: list[tuple[str, str]],
) -> dict:
    """Send up to three quick-reply buttons: (button_id, title)."""
    button_items = [
        {
            "type": "reply",
            "reply": {"id": button_id[:256], "title": title[:20]},
        }
        for button_id, title in buttons[:3]
    ]

    return await _post_message({
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body[:1024]},
            "action": {"buttons": button_items},
        },
    })


async def send_document(to: str, path: str | Path, filename: str) -> dict:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(file_path)

    if settings.dry_run:
        print(f"[WHATSAPP DRY RUN] document to={to} path={file_path}")
        return {"dry_run": True}

    if not settings.wa_token or not settings.wa_phone_id:
        raise RuntimeError("WA_TOKEN and WA_PHONE_ID must be configured")

    mime_type = mimetypes.guess_type(filename)[0] or "application/pdf"
    headers = _headers()

    async with httpx.AsyncClient(timeout=30) as client:
        with file_path.open("rb") as file_handle:
            upload = await client.post(
                _media_url(),
                headers=headers,
                data={
                    "messaging_product": "whatsapp",
                    "type": mime_type,
                },
                files={"file": (filename, file_handle, mime_type)},
            )
        upload.raise_for_status()
        media_id = upload.json()["id"]

    return await _post_message({
        "to": to,
        "type": "document",
        "document": {"id": media_id, "filename": filename},
    })