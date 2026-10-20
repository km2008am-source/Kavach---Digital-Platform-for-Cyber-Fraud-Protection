"""Simple keyword and button based intent detection."""

from kavach.contracts import IncomingMessage


MENU_WORDS = {"menu", "hi", "hello", "start", "வணக்கம்"}
LOST_MONEY_PHRASES = (
    "lost money",
    "i paid",
    "already paid",
    "money gone",
    "fraud happened",
    "பணம் போச்சு",
    "பணம் இழந்தேன்",
    "ஏமாந்துவிட்டேன்",
)


def detect(message: IncomingMessage, state: str) -> str:
    """Map an incoming message to a stable flow intent."""
    if message.button_id:
        return message.button_id

    text = message.text.strip().lower()

    # Let users escape any flow, including a stuck Golden Hour state.
    if text in MENU_WORDS:
        return "menu"

    if text.startswith("guardian "):
        return "set_guardian"

    if text in {"dns", "protect"}:
        return "dns_guide"

    if text.startswith(("news ", "verify ")):
        return "check_bait"

    if message.kind == "document" and (message.filename or "").lower().endswith(".apk"):
        return "check_apk"

    if any(phrase in text for phrase in LOST_MONEY_PHRASES):
        return "gh_start"

    if state.startswith("GH_"):
        return "gh_continue"

    return "check"