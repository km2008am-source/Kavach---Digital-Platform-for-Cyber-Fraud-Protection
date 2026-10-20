"""Bridge between Person 1's team contract (`kavach.contracts`) and the analysis engine.

The WhatsApp layer builds `kavach.contracts.AnalysisRequest` (text, language, source,
media_path, media_type, user_id) and formats `kavach.contracts.AnalysisResult` (risk_level,
scam_type, explanation, red_flags[label, explanation], recommended_action, ...). The engine
works on the richer models in `kavach.analysis.models`. Everything is converted here, so
neither side has to change.

    from kavach.analysis.scam_check import analyze     # accepts the team request directly
    from kavach.analysis.bridge import verify_bait, evidence_summary
"""
import uuid
from pathlib import Path

from kavach import contracts as team
from kavach.analysis import bait, evidence, scam_check
from kavach.analysis.models import AnalysisRequest, AnalysisResult, EvidenceExtraction, InputType

APK_MIME = "application/vnd.android.package-archive"

# Short titles for the "• {label}: {explanation}" lines in Person 1's verdict message.
FLAG_TITLES = {
    "otp_request": "Asks for OTP or PIN", "threat_arrest": "Arrest or police threat",
    "isolation": "Keep-it-secret pressure", "urgency": "Rushing you", "payment_request": "Asks for money",
    "kyc": "Fake KYC or account block", "too_good": "Too good to be true",
    "authority_claim": "Pretends to be an official", "personal_data": "Asks for personal details",
    "collect_request": "Collect request or QR trick", "apk_link": "App from a link",
    "shame_threat": "Blackmail threat", "contraband_claim": "Drugs or illegal parcel claim",
    "parcel_seized": "Seized parcel story", "prompt_injection": "Hidden trick instructions",
    "press_key": "Press a key to talk", "blocklisted_link": "Known dangerous link",
    "lookalike_domain": "Fake look-alike website", "new_domain": "Brand-new website",
    "suspicious_domain": "Risky web address", "apk_unknown_source": "App not from Play Store",
    "apk_dangerous_combo": "Can steal OTPs", "apk_sms_permission": "Reads your SMS",
    "apk_name_mismatch": "App name does not match", "apk_virustotal": "Flagged by antivirus",
    "apk_unreadable": "Unreadable file", "scam_pattern": "Matches a scam pattern",
    "ask_click": "Asks you to click", "ask_pay": "Asks you to pay", "ask_register": "Asks you to register",
    "ask_otp": "Asks for OTP", "ask_aadhaar": "Asks for Aadhaar", "ask_share": "Asks you to forward",
}

ACTIONS = {
    "report_chakshu": "Do not reply or pay. Report it on Chakshu (sancharsaathi.gov.in) and block the sender.",
    "call_1930": "Call 1930 now to report the fraud.",
    "do_not_install": "Do not install this app. Delete the file.",
    "verify_official": "Check with the organisation using the phone number on its official website.",
    "ignore": "You can ignore this message.",
    "none": "No action needed. Stay alert for requests for money, OTPs or links.",
}

VOICE_NOTE_PENDING = ("Kavach could not check this voice note yet. Please type the message, "
                      "or send a screenshot of it.")


def _input_type(req: team.AnalysisRequest) -> InputType:
    mime = (req.media_type or "").lower()
    path = (req.media_path or "").lower()
    if req.media_path:
        if APK_MIME in mime or path.endswith(".apk"):
            return InputType.apk
        if mime.startswith("image") or path.endswith((".png", ".jpg", ".jpeg", ".webp")):
            return InputType.image
    if req.source == "call":
        return InputType.transcript
    stripped = req.text.strip()
    if stripped and " " not in stripped and "." in stripped:
        return InputType.url                               # a bare link sent on its own
    return InputType.text


def to_engine(req: team.AnalysisRequest) -> AnalysisRequest:
    """Team request -> engine request. The user ID is deliberately not passed on."""
    channel = req.source if req.source in ("whatsapp", "call", "web") else "whatsapp"
    language = req.language if req.language in ("ta", "en", "hi") else "en"
    input_type = _input_type(req)
    return AnalysisRequest(request_id=uuid.uuid4().hex, channel=channel, input_type=input_type,
                           text=req.text or None, language=language,
                           file_path=req.media_path if input_type in (InputType.apk, InputType.image) else None)


def to_team(result: AnalysisResult) -> team.AnalysisResult:
    """Engine result -> team result, in the shape Person 1's `_format_verdict()` prints."""
    return team.AnalysisResult(
        risk_level=team.RiskLevel(result.risk_level),
        scam_type=result.scam_type.value,
        explanation=result.explanation_en,
        red_flags=[team.RedFlag(label=FLAG_TITLES.get(f.code, f.code.replace("_", " ").capitalize()),
                                explanation=f.label_en) for f in result.red_flags],
        recommended_action=ACTIONS.get(result.recommended_action, ACTIONS["none"]),
        confidence=None,      # engine confidence is "normal"/"lower", not a probability: don't invent one
        links=[link.model_dump() for link in result.links],
    )


def _is_voice_note_without_text(req: team.AnalysisRequest) -> bool:
    mime = (req.media_type or "").lower()
    return bool(req.media_path) and (mime.startswith("audio") or mime == "voice") and not req.text.strip()


async def analyze_team(req: team.AnalysisRequest) -> team.AnalysisResult:
    if _is_voice_note_without_text(req):
        # Speech-to-text has not run yet: say so instead of judging an empty message as safe.
        return team.AnalysisResult(risk_level=team.RiskLevel.UNKNOWN, explanation=VOICE_NOTE_PENDING)
    return to_team(await scam_check.analyze(to_engine(req)))


async def verify_bait(req: team.AnalysisRequest) -> team.AnalysisResult:
    """Scam Bait Verifier for the `check_bait` intent ("verify <post>" / "news <post>")."""
    return to_team(await bait.verify(to_engine(req)))


def to_evidence_summary(ev: EvidenceExtraction) -> team.EvidenceSummary:
    extra = {k: v for k, v in (("payee_name", ev.payee_name), ("bank_name", ev.bank_name)) if v}
    if ev.missing_fields:
        extra["missing_fields"] = ", ".join(ev.missing_fields)
    return team.EvidenceSummary(transaction_id=ev.transaction_id, amount=ev.amount, transaction_time=ev.datetime,
                                payee_upi=ev.payee_upi, scammer_number=ev.scammer_phone,
                                additional_details=extra)


async def evidence_summary(image_paths: list[str | Path]) -> team.EvidenceSummary:
    """Golden Hour: payment screenshots -> Person 1's EvidenceSummary."""
    return to_evidence_summary(await evidence.extract_evidence([str(p) for p in image_paths]))
