# M1 owns whatsapp/client.py. DRY_RUN stand-in with the frozen signatures (section 5).
# Messages are printed AND recorded in OUTBOX so tests can assert on what Call Shield sent.
from kavach.config import settings

OUTBOX: list[dict] = []


async def send_text(to: str, body: str):
    OUTBOX.append({"kind": "text", "to": to, "body": body})
    print("[DRY_RUN] text ->", to, "|", body[:200])


async def send_buttons(to: str, body: str, buttons: list[tuple[str, str]]):
    # Meta limits: max 3 buttons, title max 20 chars, body max 1000 chars
    OUTBOX.append({"kind": "buttons", "to": to, "body": body[:1000],
                   "buttons": [(i, t[:20]) for i, t in buttons[:3]]})
    print("[DRY_RUN] buttons ->", to, "|", body[:200])


async def send_document(to: str, path: str, filename: str):
    OUTBOX.append({"kind": "document", "to": to, "path": path, "filename": filename})
    print("[DRY_RUN] document ->", to, filename)
