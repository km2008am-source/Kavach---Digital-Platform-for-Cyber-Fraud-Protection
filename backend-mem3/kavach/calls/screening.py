# Member 3: Call Shield screening. Judges what a caller said and alerts the user on WhatsApp.
# No call audio is stored; the transcript lives in memory only for the length of the call
# and is never written to the logs (section 11, personal data).
import hashlib, json, logging, os, re, uuid

from kavach.config import settings
from kavach.contracts import AnalysisRequest, CallScreenResult, InputType
from kavach.analysis.scam_check import analyze
from kavach.analysis import pulse
from kavach.whatsapp.client import send_buttons, send_text
from kavach.language.service import translate

log = logging.getLogger("kavach.calls")

_HERE = os.path.dirname(__file__)
with open(os.path.join(_HERE, "official_numbers.json"), encoding="utf-8") as _f:
    OFFICIAL: dict = {k: v for k, v in json.load(_f).items() if not k.startswith("_")}

# Word-boundary patterns, so "sbi" cannot match inside another word.
_ALIAS = {org: re.compile(r"\b(?:" + "|".join(re.escape(a) for a in v["aliases"]) + r")\b", re.I)
          for org, v in OFFICIAL.items()}

BUTTONS = [("call_back", "Call back"), ("ignore", "Ignore"), ("report", "Report to Chakshu")]


def claimed_org(text: str) -> str | None:
    return next((org for org, pat in _ALIAS.items() if pat.search(text or "")), None)


def _digits(n: str) -> str:
    d = re.sub(r"\D", "", n or "")
    if d.startswith("91") and len(d) > 10:   # +91 prefix
        d = d[2:]
    return d.lstrip("0")                      # trunk 0 of landline format


def same_number(a: str, b: str) -> bool:
    da, db = _digits(a), _digits(b)
    return bool(da) and da == db


def wa_number(n: str) -> str:
    """Meta format: digits only, no '+' (integration point I6). M1's normalize_number replaces this."""
    return re.sub(r"\D", "", n or "")


def check_identity(org: str | None, caller: str) -> bool | None:
    """True/False when the organisation publishes numbers we hold; None when there is nothing to compare."""
    if not org or not OFFICIAL[org]["numbers"]:
        return None
    return any(same_number(caller, n) for n in OFFICIAL[org]["numbers"])


def reporter_hash(number: str) -> str:
    return hashlib.sha256((number + settings.HASH_SALT).encode()).hexdigest()


def build_alert(caller: str, text: str, result, org: str | None, match: bool | None) -> tuple[str, str, str]:
    """Returns (header, quote, footer), kept apart so only our own wording is translated and
    the caller's words are shown as spoken."""
    level = result.risk_level
    if match is False:
        level = "high"   # claims to be an organisation, but the number is not on its published list
    header = f"Screened call from {caller}\nRisk: {level.upper()}"
    flags = [f.label_en for f in result.red_flags[:3]]
    if match is False:
        flags.append(f"They claimed to be {org}, but this number is not on {org}'s published list.")
    if flags:
        header += "\n" + "\n".join("- " + f for f in flags)
    note = OFFICIAL.get(org or "", {}).get("note", "")
    footer = note
    quote = f'They said: "{text[:200]}"'
    return header, quote, footer


async def _translated(parts: list[str], lang: str) -> list[str]:
    out = []
    for p in parts:
        if not p or lang == "en":
            out.append(p)
            continue
        try:
            out.append(await translate(p, "en", lang))
        except Exception:
            out.append(p)   # an English alert beats no alert
    return out


async def _buttons(lang: str) -> list[tuple[str, str]]:
    titles = await _translated([t for _, t in BUTTONS], lang)
    return [(i, t[:20]) for (i, _), t in zip(BUTTONS, titles)]


def _no_recipient(call_sid: str) -> bool:
    log.error("call %s: DEMO_USER_NUMBER is not set, so there is nobody to alert", call_sid)
    return True


async def screen_transcript(call_sid: str, caller: str, text: str) -> CallScreenResult | None:
    to, lang = wa_number(settings.DEMO_USER_NUMBER), settings.DEMO_USER_LANG
    if not to and _no_recipient(call_sid):
        return None
    try:
        req = AnalysisRequest(request_id=str(uuid.uuid4()), channel="call",
                              input_type=InputType.transcript, text=text, claimed_caller=caller)
        result = await analyze(req)
        org = claimed_org(text)
        match = check_identity(org, caller)
        res = CallScreenResult(call_sid=call_sid, caller_number=caller, transcript=text,
                               claimed_org=org, official_number_match=match, analysis=result)
        header, quote, footer = build_alert(caller, text, result, org, match)
        h, f = await _translated([header, footer], lang)
        body = "\n".join(p for p in (h, quote, f) if p)[:1000]
        await send_buttons(to, body, await _buttons(lang))
        try:
            pulse.ingest(result, text, None, reporter_hash(settings.DEMO_USER_NUMBER))
        except Exception:
            log.warning("pulse.ingest failed for call %s", call_sid)
        log.info("call %s screened: risk=%s org=%s match=%s", call_sid, result.risk_level, org, match)
        return res
    except Exception:
        # Whatever broke, the user still hears about the call.
        log.exception("screening failed for call %s", call_sid)
        msg = (f"A call from {caller} was screened but could not be analysed. "
               "Treat it as unverified. Do not share OTPs, and do not pay anyone because of this call.")
        (msg,) = await _translated([msg], lang)
        await send_text(to, msg)
        return None


async def screen_hangup(call_sid: str, caller: str) -> CallScreenResult:
    to, lang = wa_number(settings.DEMO_USER_NUMBER), settings.DEMO_USER_LANG
    if not to and _no_recipient(call_sid):
        return CallScreenResult(call_sid=call_sid, caller_number=caller, hung_up_without_reason=True)
    msg = (f"A caller from {caller} ended the call without giving a reason. "
           "Scam call centres often do this. Do not call back unless you know them.")
    (msg,) = await _translated([msg], lang)
    await send_text(to, msg)
    log.info("call %s: no reason given", call_sid)
    return CallScreenResult(call_sid=call_sid, caller_number=caller, hung_up_without_reason=True)
