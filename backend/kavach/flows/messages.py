"""English source templates for user-facing messages."""

WELCOME = (
    "Welcome to Kavach. Send a suspicious message, link, screenshot, or APK "
    "for a safety check. If you have already lost money, say “I lost money”."
)

UNSUPPORTED = (
    "I can check text, links, screenshots, voice notes, and APK files. "
    "Send one of those, or type “menu”."
)

ANALYSIS_UNAVAILABLE = (
    "I couldn't complete that safety check right now. Please don't open the "
    "link or install the file. If money may be at risk, call 1930."
)

GOLDEN_HOUR_START = (
    "If you lost money, call 1930 now. While you contact them, send screenshots "
    "of the payment and conversation here. Type “menu” to leave this flow."
)

GOLDEN_HOUR_WAITING = (
    "Send any payment or chat screenshots now. When you've sent them all, "
    "tap Done. Do not send passwords, PINs, or OTPs."
)

GOLDEN_HOUR_NO_EVIDENCE = (
    "I don't have any evidence images yet. Send a screenshot, or tap Done "
    "to continue with details you can provide."
)

GOLDEN_HOUR_ASK_BANK = (
    "Which bank account or payment method did the money leave from? "
    "Tell me the bank name. Meanwhile, contact your bank using its official "
    "app or website and ask them to block further transactions."
)

GOLDEN_HOUR_ACK = (
    "When you receive an acknowledgement number from 1930, send it here. "
    "Then file the full complaint at cybercrime.gov.in."
)

GUARDIAN_USAGE = (
    "To set a trusted contact, send: guardian followed by their phone number. "
    "Example: guardian +919876543210"
)

DNS_GUIDE = (
    "Private DNS can block some known malicious domains. On many Android phones: "
    "Settings → Network & Internet → Private DNS. Choose a reputable provider "
    "and follow its official setup instructions. Menu names vary by phone."
)

GENERIC_ERROR = (
    "Something went wrong while handling that message. Type “menu” to restart. "
    "If money may be at risk, call 1930 now."
)
EVIDENCE_FIELD_PROMPTS = {
    "transaction_id": "Enter the transaction or UPI reference ID, or tap Skip.",
    "amount": "Enter the amount lost, or tap Skip.",
    "transaction_time": "Enter the transaction date and time, or tap Skip.",
    "payee_upi": "Enter the recipient UPI ID, if known, or tap Skip.",
    "scammer_number": "Enter the scammer's phone number, if known, or tap Skip.",
}

EVIDENCE_REVIEW = (
    "Thank you. I’ll include the details you provided in the evidence pack. "
    "If a detail is missing, it will be marked as not provided."
)