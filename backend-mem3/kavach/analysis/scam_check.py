# STAND-IN for Member 2's analysis/scam_check.py (same signature as section 5).
# Keyword rules only, enough for Member 3 to test Call Shield and /api/analyze.
# Replaced by M2's real pipeline at the H12 integration; nothing in M3's code depends on how it works.
import re, time
from kavach.contracts import (AnalysisRequest, AnalysisResult, Entities, RedFlag, ScamType)

_FLAGS = {  # code: (weight, keywords, plain-words label)
    "otp_request": (35, ["otp", "verification code"], "They ask for a code that only you should see."),
    "threat_arrest": (30, ["arrest", "warrant", "cbi", "police", "illegal", "drugs"], "They threaten you with arrest or a police case."),
    "urgency": (15, ["immediately", "within 24 hours", "blocked", "suspended", "today"], "They push you to act in a hurry."),
    "payment_request": (25, ["pay", "fine", "transfer", "fee", "deposit"], "They ask you to send money."),
    "kyc": (20, ["kyc", "pan update"], "Banks do not ask you to update KYC through a call or link."),
    "authority": (15, ["customs", "officer", "inspector", "bureau"], "They claim to be an official to make you obey."),
}
_URL = re.compile(r"(?:https?://|www\.)\S+")


async def analyze(req: AnalysisRequest) -> AnalysisResult:
    t0 = time.time()
    text = (req.text or "").lower()
    score, flags = 0, []
    for code, (w, words, label) in _FLAGS.items():
        if any(k in text for k in words):
            score += w
            flags.append(RedFlag(code=code, label_en=label))
    score = min(score, 100)
    level = "high" if score >= 70 else "medium" if score >= 40 else "low"
    if "customs" in text or "parcel" in text:
        stype = ScamType.courier_customs
    elif "arrest" in text or "cbi" in text:
        stype = ScamType.digital_arrest
    elif "kyc" in text:
        stype = ScamType.kyc_update
    else:
        stype = ScamType.unknown if score else ScamType.not_scam
    return AnalysisResult(
        request_id=req.request_id, risk_level=level, risk_score=score, scam_type=stype,
        red_flags=flags[:4], confidence="lower",
        explanation_en="This looks risky." if score >= 40 else "Nothing obviously risky was found.",
        recommended_action="report_chakshu" if score >= 40 else "none",
        entities=Entities(urls=_URL.findall(req.text or "")),
        latency_ms=int((time.time() - t0) * 1000))
