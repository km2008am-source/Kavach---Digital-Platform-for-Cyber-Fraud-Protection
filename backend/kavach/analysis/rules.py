"""Regex entities and keyword red flags: instant, explainable, and working when the LLM is down.

English keywords match on word boundaries (so "pay" does not fire on "Paytm").
Tamil and romanised-Hindi keywords match as substrings, because Tamil words take
suffixes (கைது -> கைது செய்யப்பட்டுள்ளீர்கள்). Tamil and Hindi lists need a native
speaker's review before the demo.
"""
import re

from kavach.analysis.models import RedFlag, ScamType

PHONE = re.compile(r"(?<![\d+])(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)")
UPI = re.compile(r"\b[\w.\-]{2,}@[a-zA-Z]{2,}\b(?!\.[a-zA-Z])")       # skip e-mail addresses
_TLDS = r"xyz|top|in|com|co|info|link|online|site|me|ly|net|org|live|shop|click|icu|buzz|app"
# Scheme/www links, or bare domains like "pan-link-kyc.xyz" (with or without a path). The
# look-behind stops e-mail domains ("ravi@gmail.com") being read as links.
URL = re.compile(r"(?:https?://|www\.)\S+"
                 r"|(?<![@\w.-])[a-z0-9][\w-]*(?:\.[\w-]+)*\.(?:" + _TLDS + r")\b(?:/\S*)?", re.I)
AMOUNT = re.compile(r"(?:₹|\brs\.?|\binr)\s?\d[\d,]*(?:\.\d+)?|\d[\d,]*\s?(?:ரூபாய்|rupees)", re.I)
UPI_REF = re.compile(r"(?<!\d)\d{12}(?!\d)")

# code: (weight, English keywords, Tamil / romanised-Hindi substrings, plain-English label)
KEYWORDS: dict[str, tuple[int, list[str], list[str], str]] = {
    "otp_request": (35,
        ["share the otp", "share otp", "send the otp", "send otp", "tell the otp", "otp to continue",
         "share the verification code", "verification code sent", "enter your upi pin", "upi pin"],
        ["ஓடிபி அனுப்ப", "ஓடிபி சொல்", "பின் எண்ணை உள்ளிட", "otp batayein", "otp bataiye"],
        "It asks for your OTP or UPI PIN. No bank, police or company ever asks for these."),
    "threat_arrest": (30,
        ["arrest", "arrested", "warrant", "cbi", "police case", "digital arrest", "narcotics",
         "money laundering", "court action", "case will be filed", "illegal activity",
         "investigating officer", "illegal parcel", "crime branch", "investigation", "inquiry", "fir", "legal proceedings", "legal action", "terror funding", "hawala", "enforcement directorate", "non-cooperation"],
        ["கைது", "வழக்கு", "போலீஸ்", "சிபிஐ", "giraftar", "police case", "பயங்கரவாத", "விசாரணை", "fir hogi", "giraftaar"],
        "It threatens you with arrest or a police case. Real police never do this on a call or message."),
    "isolation": (20,
        ["don't tell", "do not tell", "do not inform", "stay on the call", "stay on the video call",
         "confidential", "do not disconnect", "do not share this offer", "keep your camera on", "video call", "skype call", "remain on this", "until the inquiry", "do not inform your family", "leaving it"],
        ["யாரிடமும் சொல்ல வேண்டாம்", "துண்டிக்க வேண்டாம்", "kisi ko mat batana", "bane rahiye", "வீடியோ அழைப்பில்", "கூற வேண்டாம்", "சொல்ல வேண்டாம்", "kisi ko na batayen"],
        "It tells you to keep it secret or stay on the call, so nobody can warn you."),
    "urgency": (15,
        ["immediately", "within 24 hours", "within 2 hours", "today only", "today", "blocked",
         "suspended", "suspension", "disconnected", "expired", "expires", "last date", "limited slots",
         "right now", "tonight", "before offer ends", "deactivated in", "urgent"],
        ["உடனே", "இன்றே", "இன்று மட்டுமே", "இப்போதே", "முடக்கப்படும்", "turant", "abhi", "aaj hi",
         "band ho jayega", "seats limited", "இரவுக்குள்", "நிறுத்தப்படும்", "jaldi"],
        "It rushes you so you act before you can think or check."),
    "payment_request": (20,
        ["pay", "transfer", "processing fee", "refundable deposit", "deposit", "registration fee",
         "fee", "customs clearance", "send money", "invest", "charge", "charges", "duty", "tax", "capital", "registration charge"],
        ["பணம் அனுப்ப", "செலுத்த", "கட்டணம்", "transfer kijiye", "registration fee", "முன்பணம்", "jama karein", "lagaiye"],
        "It asks you to pay or transfer money."),
    "kyc": (20,
        ["kyc", "pan update", "pan is not linked", "account will be blocked", "power connection", "re-kyc", "pan card", "deactivated", "re-verify", "restricted"],
        ["kyc", "பான் கார்டு", "khata block"],
        "Banks never ask you to update KYC or PAN through a message or link."),
    "too_good": (20,
        ["you have won", "lottery", "lucky draw", "work from home", "earn daily", "guaranteed",
         "double your money", "returns", "cashback", "free laptop", "won", "prize", "commission",
         "sure-shot", "winner", "giveaway", "pre-approved", "0% interest", "without documents", "eligible for a refund", "part time", "part-time", "rating tasks", "liking", "free recharge", "profit every day"],
        ["வென்றுள்ளீர்கள்", "லாட்டரி", "இரட்டிப்பு", "இலவச", "சம்பாதிக்கலாம்", "கேஷ்பேக்",
         "வீட்டில் இருந்தே", "ghar baithe", "kamaayein", "வருமானம் பெறுங்கள்", "லைக் செய்து", "பரிசு", "பகுதி நேர", "inaam", "jeeta", "pakka"],
        "The offer is too good to be true: easy money, prizes or guaranteed returns."),
    "authority_claim": (15,
        ["inspector", "customs officer", "customs", "cyber crime", "officer", "rbi verification", "crime branch", "dcp", "income tax department", "enforcement directorate"],
        ["அதிகாரி", "சுங்க", "cbi officer", "சைபர் கிரைம்", "officer se baat"],
        "It claims to be from police, customs or a government office to scare you."),
    "personal_data": (20,
        ["aadhaar and bank details", "bank details", "card details", "aadhaar number", "account details", "only aadhaar", "all permissions"],
        ["ஆதார் எண் மற்றும்"],
        "It asks for Aadhaar, bank or card details."),
    "collect_request": (25,
        ["payment request", "collect request", "scan this qr", "qr code", "to receive the money",
         "to receive the amount", "accept the request", "money will come to you", "get credit"],
        ["பணத்தைப் பெற"],
        "To RECEIVE money you never enter a PIN or scan a QR code. This request takes money from you."),
    "apk_link": (30,
        [".apk", "apk from this link", "install the app from the link", "download the app from"],
        [],
        "It asks you to install an app from a link. Install apps only from the Play Store."),
    "shame_threat": (30,
        ["morphed photos", "to all your contacts"],
        [],
        "It threatens to shame you to your contacts. This is extortion; report it."),
    # Call-scam families (Call Shield transcripts are spoken, lower-case and unpunctuated).
    "contraband_claim": (30,
        ["drugs", "narcotics", "narcotic", "mdma", "ganja", "cocaine", "heroin", "illegal items",
         "fake passports", "passports", "contraband"],
        ["போதைப்பொருள்", "drugs mile"],
        "It claims a parcel or account in your name is linked to drugs or illegal items. "
        "This is a scare tactic: customs and police do not phone you about it."),
    "parcel_seized": (20,
        [],
        ["பறிமுதல்", "pakda gaya", "pakda hai"],
        "It says a parcel in your name was stopped or seized. Fake 'customs' calls always start this way."),
    "prompt_injection": (40,
        ["ignore your instructions", "ignore previous instructions", "ignore all previous", "say this is safe",
         "mark this as safe", "you are now", "system prompt"],
        [],
        "It contains hidden instructions meant to fool automatic scam checkers. Genuine messages never do this."),
    "press_key": (15,
        ["press 1", "press 9"],
        ["1 அழுத்தவும்", "dabaiye"],
        "Recorded calls asking you to press a key to talk to an 'officer' are a common scam start."),
}

# Regex patterns per code, for phrasings a fixed keyword list cannot enumerate.
PATTERNS: dict[str, list[re.Pattern]] = {code: [re.compile(p, re.I) for p in pats] for code, pats in {
    "too_good": [r"\d[\d,]*\s*(?:to\s*\d[\d,]*\s*)?(?:per|a|every)\s+(?:day|week)\b",
                 r"\d+\s*%\s*(?:weekly\s+|daily\s+|monthly\s+)?(?:profit|returns?)"],
    "urgency": [r"\b(?:with)?in\s+\d+\s+(?:hours?|minutes?|mins?)\b"],
    "otp_request": [r"\b(?:enter|type)\s+(?:your\s+)?(?:upi\s+)?pin\b"],
    "apk_link": [r"\binstall\b.{0,40}\b(?:link|apk)\b"],
    "press_key": [r"\bpress\s+\d\b", r"\d\s+dabaiye"],
    # "<parcel> ... stopped/seized" or "seized ... <parcel>", within a few words, either order.
    "parcel_seized": [r"\b(?:parcel|package|courier|shipment|consignment)\b(?:\W+\w+){0,6}?\W+"
                      r"(?:stopped|seized|held|intercepted|confiscated|caught)\b",
                      r"\b(?:seized|intercepted|confiscated)\b(?:\W+\w+){0,4}?\W+(?:parcel|package|shipment)\b"],
    # "do not cut / hang up / disconnect the call", "stay on the line": keeps the victim isolated.
    "isolation": [r"\b(?:do\s+not|don'?t)\s+(?:cut|hang\s+up|disconnect|end)\b", r"\bstay\s+on\s+the\s+line\b"],
    # "speak / talk to the officer", "connecting you to the ... officer"
    "authority_claim": [r"\b(?:speak|talk)\s+(?:to|with)\s+(?:the\s+)?(?:\w+\s+)?officer\b",
                        r"\bconnecting\s+you\s+to\b"],
}.items()}

# Ordered: the first matching type wins.
_TYPE_HINTS: list[tuple[ScamType, list[str]]] = [
    (ScamType.digital_arrest, ["digital arrest", "டிஜிட்டல் கைது"]),
    (ScamType.loan_app, ["loan"]),
    (ScamType.courier_customs, ["parcel", "customs", "fedex", "dhl", "courier", "package", "india post",
                                "சுங்க", "பார்சல்", "கூரியர்"]),
    (ScamType.fake_scheme, ["yojana", "scheme", "திட்டம்", "government is giving"]),
    (ScamType.lottery_prize, ["lottery", "lucky draw", "prize", "you have won", "won an", "contest",
                              "லாட்டரி", "வென்று"]),
    (ScamType.investment, ["invest", "returns", "stock", "crypto", "ipo", "trading", "முதலீடு", "லாபம்"]),
    (ScamType.job_offer, ["job", "work from home", "task", "salary", "வேலை", "kaam karein"]),
    (ScamType.upi_collect, ["collect request", "payment request", "upi pin", "qr code", "cashback",
                            "பின் எண்"]),
    (ScamType.kyc_update, ["kyc", "pan", "electricity", "account will be blocked"]),
]


def _matches(keyword: str, text_lower: str) -> bool:
    if keyword.startswith("."):          # ".apk": suffix match, no leading word boundary
        return keyword in text_lower
    return re.search(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", text_lower) is not None


def extract_entities(text: str) -> dict[str, list[str]]:
    urls = [u.rstrip(".,!?;:)\"'") for u in URL.findall(text)]
    return {"phones": PHONE.findall(text), "upi_ids": UPI.findall(text),
            "urls": list(dict.fromkeys(urls)), "amounts": AMOUNT.findall(text)}


def rule_flags(text: str) -> tuple[int, list[str]]:
    t, score, codes = text.lower(), 0, []
    for code, (w, en, local, _label) in KEYWORDS.items():
        if any(_matches(k, t) for k in en) or any(k.lower() in t for k in local) \
                or any(p.search(text) for p in PATTERNS.get(code, [])):
            score += w
            codes.append(code)
    return min(score, 100), codes


def red_flag(code: str) -> RedFlag:
    return RedFlag(code=code, label_en=KEYWORDS[code][3])


def infer_scam_type(text: str, codes: list[str], has_url: bool) -> ScamType:
    """Rules-only scam type, used when the LLM is unavailable."""
    t = text.lower()
    if "threat_arrest" in codes and ("isolation" in codes or "authority_claim" in codes) \
            and not any(k in t for k in ("parcel", "customs", "fedex", "dhl", "சுங்க", "பார்சல்")):
        return ScamType.digital_arrest
    for scam_type, hints in _TYPE_HINTS:
        if any(h in t for h in hints):
            return scam_type
    if "threat_arrest" in codes:
        return ScamType.digital_arrest
    if has_url or "apk_link" in codes:
        return ScamType.phishing_link
    return ScamType.unknown if codes else ScamType.not_scam
