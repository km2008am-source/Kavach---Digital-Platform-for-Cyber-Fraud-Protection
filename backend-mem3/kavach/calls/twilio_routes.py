# Member 3: Call Shield, Twilio voice webhooks (section 8-G).
# Answer with a recorded notice, collect the caller's reason as speech, hand off to screening.
import logging, os
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import Gather, VoiceResponse

from kavach.calls.screening import screen_hangup, screen_transcript
from kavach.config import settings

log = logging.getLogger("kavach.calls")
router = APIRouter()

NOTICE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "screening_notice.mp3")
NOTICE_TEXT = ("This call is being screened by an automated assistant. "
               "Please say your name and why you are calling.")

# CallSids that gave a reason. Only IDs are kept (never what was said), and only until the call ends.
_screened: set[str] = set()


async def _form(request: Request) -> dict:
    """Parse the Twilio form post and prove it came from Twilio (X-Twilio-Signature)."""
    form = {k: str(v) for k, v in (await request.form()).items()}
    url = settings.PUBLIC_BASE_URL + request.url.path
    if request.url.query:
        url += "?" + request.url.query
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    if not settings.TWILIO_AUTH_TOKEN or not validator.validate(
            url, form, request.headers.get("X-Twilio-Signature", "")):
        raise HTTPException(status_code=403, detail="not from Twilio")
    return form


def twiml(vr: VoiceResponse) -> Response:
    return Response(str(vr), media_type="application/xml")


@router.post("/twilio/voice")
async def voice(request: Request):
    await _form(request)
    vr = VoiceResponse()
    g = Gather(input="speech", action="/twilio/gather", method="POST",
               language=settings.CALL_SPEECH_LANG, speech_timeout="auto", timeout=6)
    if os.path.exists(NOTICE_PATH):
        g.play(settings.PUBLIC_BASE_URL + "/static/screening_notice.mp3")
    else:   # recording not made yet: say the notice so the call still works
        g.say(NOTICE_TEXT, language="en-IN")
    vr.append(g)
    vr.say("No reason was given. Goodbye.", language="en-IN")
    vr.hangup()
    return twiml(vr)


@router.post("/twilio/gather")
async def gather(request: Request, bg: BackgroundTasks):
    f = await _form(request)
    sid, text = f.get("CallSid", ""), f.get("SpeechResult", "").strip()
    vr = VoiceResponse()
    if text:
        _screened.add(sid)
        bg.add_task(screen_transcript, sid, f.get("From", ""), text)
        vr.say("Thank you. The person you called will decide whether to call you back.", language="en-IN")
    else:
        vr.say("No reason was given. Goodbye.", language="en-IN")
    vr.hangup()
    return twiml(vr)


@router.post("/twilio/status")
async def status(request: Request, bg: BackgroundTasks):
    f = await _form(request)
    sid = f.get("CallSid", "")
    if f.get("CallStatus") == "completed":
        if sid not in _screened:   # call ended and nobody gave a reason
            bg.add_task(screen_hangup, sid, f.get("From", ""))
        _screened.discard(sid)   # nothing about the call is kept after it ends
    return {"ok": True}
