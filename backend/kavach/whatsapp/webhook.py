"""WhatsApp webhook verification, parsing, and message dispatch."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from kavach.config import settings
from kavach.contracts import IncomingMessage
from kavach.db import session
from kavach.flows.engine import handle_message
from datetime import datetime, timezone
from urllib.parse import parse_qs

from fastapi import Response
from twilio.request_validator import RequestValidator

from kavach.whatsapp.client import send_text
import hmac



router = APIRouter()


@router.get("/webhook/whatsapp", response_class=PlainTextResponse)
async def verify_webhook(
    mode: str | None = Query(default=None, alias="hub.mode"),
    token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    if (
        mode == "subscribe"
        and settings.wa_verify_token
        and token == settings.wa_verify_token
        and challenge is not None
    ):
        return challenge

    raise HTTPException(status_code=403, detail="Webhook verification failed")


def _extract_messages(payload: dict[str, Any]) -> list[IncomingMessage]:
    messages: list[IncomingMessage] = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            for message in value.get("messages", []):
                message_type = message.get("type", "unknown")
                sender = message.get("from")
                message_id = message.get("id")

                if not sender or not message_id:
                    continue

                parsed = IncomingMessage(
                    sender=sender,
                    message_id=message_id,
                    kind=message_type,
                    timestamp=message.get("timestamp"),
                )

                if message_type == "text":
                    parsed.text = message.get("text", {}).get("body", "")

                elif message_type == "interactive":
                    interactive = message.get("interactive", {})
                    button_reply = interactive.get("button_reply", {})
                    list_reply = interactive.get("list_reply", {})
                    parsed.button_id = (
                        button_reply.get("id") or list_reply.get("id")
                    )
                    parsed.text = (
                        button_reply.get("title") or list_reply.get("title") or ""
                    )

                elif message_type in {"image", "audio", "document", "video"}:
                    media = message.get(message_type, {})
                    parsed.media_id = media.get("id")
                    parsed.mime_type = media.get("mime_type")
                    parsed.filename = media.get("filename")
                    parsed.text = media.get("caption", "")

                messages.append(parsed)

    return messages


def _claim_message_id(message_id: str) -> bool:
    """Atomically record an ID; return False if Meta already delivered it."""
    with session() as connection:
        cursor = connection.execute(
            "INSERT OR IGNORE INTO processed_messages (message_id) VALUES (?)",
            (message_id,),
        )
        return cursor.rowcount == 1


@router.post("/webhook/whatsapp")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, bool]:
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Expected JSON object")

    for message in _extract_messages(payload):
        if _claim_message_id(message.message_id):
            background_tasks.add_task(handle_message, message)

    # Acknowledge promptly; message processing happens after the response.
    return {"ok": True}
def _twilio_button_id(body: str) -> str | None:
    return {
        "i already paid": "gh_start",
        "how to report": "report",
        "menu": "menu",
        "done": "gh_done",
    }.get(body.strip().casefold())


@router.post("/webhook/twilio")
async def receive_twilio_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> Response:
    if settings.whatsapp_provider != "twilio":
        raise HTTPException(status_code=404, detail="Twilio webhook is disabled")

    if not settings.twilio_auth_token or not settings.twilio_webhook_url:
        raise HTTPException(status_code=503, detail="Twilio webhook is not configured")

    raw_body = await request.body()
    parsed = parse_qs(raw_body.decode("utf-8"), keep_blank_values=True)
    fields = {key: values[-1] for key, values in parsed.items()}

    signature = request.headers.get("X-Twilio-Signature", "")
    validator = RequestValidator(settings.twilio_auth_token)

    if not validator.validate(
        settings.twilio_webhook_url,
        fields,
        signature,
    ):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    sender = fields.get("From", "")
    message_id = fields.get("MessageSid", "")
    body = fields.get("Body", "")

    if not sender or not message_id:
        raise HTTPException(status_code=400, detail="Missing sender or message ID")

    # Media downloads are not wired to Twilio yet. Give the user a clear
    # response rather than passing a Twilio media URL to Meta's downloader.
    if int(fields.get("NumMedia", "0") or "0") > 0:
        background_tasks.add_task(
            send_text,
            sender,
            "For this Twilio demo, please send the suspicious message as text. "
            "Image and voice-note processing will be connected next.",
        )
        return Response(
            content="<Response/>",
            media_type="application/xml",
        )

    if _claim_message_id(message_id):
        message = IncomingMessage(
            sender=sender.removeprefix("whatsapp:"),
            message_id=message_id,
            kind="text",
            text=body,
            button_id=_twilio_button_id(body),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        background_tasks.add_task(handle_message, message)

    return Response(
        content="<Response/>",
        media_type="application/xml",
    )
@router.post("/webhook/telegram")
async def receive_telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, bool]:
    if settings.whatsapp_provider != "telegram":
        raise HTTPException(status_code=404, detail="Telegram webhook is disabled")

    expected_secret = settings.telegram_webhook_secret
    received_secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token",
        "",
    )

    if not expected_secret or not hmac.compare_digest(
        received_secret,
        expected_secret,
    ):
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")

    try:
        update = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    message_data = update.get("message")
    if not isinstance(message_data, dict):
        return {"ok": True}

    chat = message_data.get("chat", {})
    chat_id = chat.get("id")
    message_id = message_data.get("message_id")

    if chat_id is None or message_id is None:
        return {"ok": True}

    photo_sizes = message_data.get("photo") or []
    voice = message_data.get("voice") or {}
    audio = message_data.get("audio") or {}
    document = message_data.get("document") or {}
    text = message_data.get("text") or message_data.get("caption") or ""

    kind = "text"
    media_id = None
    mime_type = None
    filename = None

    if photo_sizes:
        # Telegram lists several sizes; use the largest available photo.
        photo = max(
            photo_sizes,
            key=lambda item: item.get("file_size", 0),
        )
        kind = "image"
        media_id = photo.get("file_id")
        mime_type = "image/jpeg"
        filename = f"telegram-{message_id}.jpg"

    elif voice or audio:
        media = voice or audio
        kind = "audio"
        media_id = media.get("file_id")
        mime_type = media.get("mime_type") or ("audio/ogg" if voice else "audio/mpeg")
        suffix = ".ogg" if voice else ".mp3"
        filename = media.get("file_name") or f"telegram-{message_id}{suffix}"

    elif document:
        kind = "document"
        media_id = document.get("file_id")
        mime_type = document.get("mime_type") or "application/octet-stream"
        filename = document.get("file_name") or f"telegram-{message_id}"

    if text.strip().startswith("/start"):
        text = "menu"

    message = IncomingMessage(
        sender=str(chat_id),
        message_id=f"telegram:{chat_id}:{message_id}",
        kind=kind,
        text=text,
        media_id=media_id,
        mime_type=mime_type,
        filename=filename,
        button_id=_twilio_button_id(text) if text else None,
        timestamp=str(message_data.get("date", "")),
    )

    if _claim_message_id(message.message_id):
        background_tasks.add_task(handle_message, message)

    return {"ok": True}