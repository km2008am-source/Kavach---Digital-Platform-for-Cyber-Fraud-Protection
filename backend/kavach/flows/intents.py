"""Simple keyword and button based intent detection."""

from kavach.contracts import IncomingMessage


MENU_WORDS = {
    "menu",
    "hi",
    "hello",
    "start",
    "मेन्यू",
    "नमस्ते",
    "नमस्कार",
    "शुरू",
}

LOST_MONEY_PHRASES = (
    "lost money",
    "i paid",
    "already paid",
    "money gone",
    "fraud happened",
    "मेरे पैसे चले गए",
    "मेरे पैसे खो गए",
    "मैंने पैसे गंवा दिए",
    "मेरे साथ धोखाधड़ी हुई",
    "मैं ठगी का शिकार हुआ",
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

    evidence_states = {
    "GH_TRANSACTION_ID",
    "GH_AMOUNT",
    "GH_TRANSACTION_TIME",
    "GH_PAYEE_UPI",
    "GH_SCAMMER_NUMBER",
    }
    if state in evidence_states and text in {"skip", "छोड़ें", "छोड़ दो", "छोड़ना"}:
        return "gh_skip"

    if state.startswith("GH_"):
        return "gh_continue"

    return "check"