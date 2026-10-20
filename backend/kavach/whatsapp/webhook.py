"""WhatsApp webhook verification, parsing, and message dispatch."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from kavach.config import settings
from kavach.contracts import IncomingMessage
from kavach.db import session
from kavach.flows.engine import handle_message


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
