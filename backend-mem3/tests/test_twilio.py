import json, logging, os
import pytest

from kavach.calls import screening
from kavach.config import settings
from kavach.calls.screening import claimed_org, check_identity, same_number
from kavach.whatsapp import client as wa
from tests.conftest import signed_post, DEMO

# Exact line Member 2 says in the demo (pitch/demo_script.md). With Member 2's real engine and the
# LLM off, the shorter "customs... drugs... pay a fine" scores only MEDIUM; this full line scores HIGH.
CUSTOMS = "I am calling from the customs office, your parcel has illegal items, pay a fine or face arrest"


# ---- signature -------------------------------------------------------------------------
@pytest.mark.parametrize("path", ["/twilio/voice", "/twilio/gather", "/twilio/status"])
def test_unsigned_request_is_rejected(client, path):
    r = client.post(path, data={"CallSid": "CA1", "From": "+911"})
    assert r.status_code == 403
    assert "<Response" not in r.text          # no TwiML for a forged call


def test_wrong_signature_is_rejected(client):
    r = client.post("/twilio/voice", data={"CallSid": "CA1"}, headers={"X-Twilio-Signature": "nope"})
    assert r.status_code == 403


def test_missing_auth_token_rejects_everything(client, monkeypatch):
    from kavach.config import settings
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "")
    assert signed_post(client, "/twilio/voice", {"CallSid": "CA1"}).status_code == 403


# ---- voice notice ----------------------------------------------------------------------
def test_voice_returns_gather_with_notice(client):
    r = signed_post(client, "/twilio/voice", {"CallSid": "CA1", "From": "+919811111111"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/xml")
    assert '<Gather' in r.text and 'input="speech"' in r.text and 'action="/twilio/gather"' in r.text
    assert "screened by an automated assistant" in r.text or "screening_notice.mp3" in r.text


# ---- gather -> alert -------------------------------------------------------------------
def test_gather_sends_high_alert_with_three_buttons(client):
    r = signed_post(client, "/twilio/gather",
                    {"CallSid": "CA2", "From": "+919822222222", "SpeechResult": CUSTOMS})
    assert r.status_code == 200 and "<Hangup" in r.text
    assert len(wa.OUTBOX) == 1
    m = wa.OUTBOX[0]
    assert m["kind"] == "buttons"
    assert m["to"] == "919800000000"                      # digits only, no '+' (I6)
    assert "Risk: HIGH" in m["body"] and len(m["body"]) <= 1000
    assert [b[0] for b in m["buttons"]] == ["call_back", "ignore", "report"]
    assert all(len(t) <= 20 for _, t in m["buttons"])


def test_gather_without_speech_sends_no_alert_yet(client):
    r = signed_post(client, "/twilio/gather", {"CallSid": "CA3", "From": "+919833333333"})
    assert r.status_code == 200 and not wa.OUTBOX
    # the status callback then raises the "no reason" alert
    signed_post(client, "/twilio/status", {"CallSid": "CA3", "From": "+919833333333", "CallStatus": "completed"})
    assert len(wa.OUTBOX) == 1 and "without giving a reason" in wa.OUTBOX[0]["body"]


# ---- hang-up ---------------------------------------------------------------------------
def test_hangup_during_notice_alerts(client):
    r = signed_post(client, "/twilio/status", {"CallSid": "CA4", "From": "+919844444444", "CallStatus": "completed"})
    assert r.status_code == 200
    assert len(wa.OUTBOX) == 1
    assert wa.OUTBOX[0]["kind"] == "text" and "+919844444444" in wa.OUTBOX[0]["body"]


def test_normal_call_is_not_double_alerted_on_completion(client):
    signed_post(client, "/twilio/gather", {"CallSid": "CA5", "From": "+919855555555", "SpeechResult": CUSTOMS})
    assert len(wa.OUTBOX) == 1
    signed_post(client, "/twilio/status", {"CallSid": "CA5", "From": "+919855555555", "CallStatus": "completed"})
    assert len(wa.OUTBOX) == 1                            # no extra hang-up alert


def test_non_completed_status_is_ignored(client):
    signed_post(client, "/twilio/status", {"CallSid": "CA6", "From": "+919866666666", "CallStatus": "ringing"})
    assert not wa.OUTBOX


# ---- identity check --------------------------------------------------------------------
def test_claimed_sbi_from_unlisted_number_is_flagged(client):
    signed_post(client, "/twilio/gather", {"CallSid": "CA7", "From": "+919877777777",
                                           "SpeechResult": "I'm calling from SBI about your account"})
    body = wa.OUTBOX[0]["body"]
    assert "claimed to be SBI" in body and "not on SBI's published list" in body
    assert "Risk: HIGH" in body                           # raised by the identity mismatch


def test_claimed_sbi_from_published_number_is_not_flagged():
    assert check_identity("SBI", "18001234") is True
    assert check_identity("SBI", "+919449112211") is True  # mobile helpline, E.164 form
    assert check_identity("SBI", "+919877777777") is False


def test_agency_claim_has_no_number_to_compare():
    assert claimed_org("this is the CBI") == "CBI"
    assert check_identity("CBI", "+919800000001") is None  # cannot compare, so no false claim


async def test_agency_note_is_shown(client):
    res = await screening.screen_transcript("CA8", "+919888888888", "This is the CBI, you will be arrested")
    assert res.official_number_match is None
    assert "do not ask for money" in wa.OUTBOX[0]["body"]


def test_org_match_uses_word_boundaries():
    assert claimed_org("sbibank offer") is None
    assert claimed_org("a fedex parcel") == "Courier"
    assert claimed_org("") is None and claimed_org(None) is None


def test_number_normalisation():
    assert same_number("+91 94491 12211", "9449112211")
    assert same_number("080-26599990", "+91 80 2659 9990")
    assert not same_number("", "")
    assert not same_number("+919800000001", "+919800000002")


def test_official_numbers_match_the_sbi_page_as_printed():
    """Numbers as printed on https://sbi.bank.in/web/customer-care/contact-us/ (retrieved 2026-10-20)."""
    printed = ["1800 1234", "1800 2100", "1800 11 2211", "1800 425 3800", "080-26599990",
               "1800 11 1109", "94491 12211"]
    stored = screening.OFFICIAL["SBI"]["numbers"]
    assert len(stored) == len(printed)
    for p in printed:
        assert any(same_number(p, s) for s in stored), p
    assert screening.OFFICIAL["SBI"]["source"].startswith("https://sbi.bank.in")


def test_every_org_with_numbers_records_a_source():
    for org, v in screening.OFFICIAL.items():
        if v["numbers"]:
            assert v["source"] and v["retrieved"], org


# ---- failure and privacy ---------------------------------------------------------------
async def test_analysis_failure_still_alerts_the_user(monkeypatch):
    async def boom(req): raise RuntimeError("analysis down")
    monkeypatch.setattr(screening, "analyze", boom)
    res = await screening.screen_transcript("CA9", "+919899999999", CUSTOMS)
    assert res is None
    assert len(wa.OUTBOX) == 1 and "could not be analysed" in wa.OUTBOX[0]["body"]


async def test_translation_failure_falls_back_to_english(monkeypatch):
    from kavach.config import settings
    monkeypatch.setattr(settings, "DEMO_USER_LANG", "ta")
    async def boom(*a, **k): raise RuntimeError("translate down")
    monkeypatch.setattr(screening, "translate", boom)
    await screening.screen_transcript("CA10", "+919800000010", CUSTOMS)
    assert len(wa.OUTBOX) == 1 and "Risk: HIGH" in wa.OUTBOX[0]["body"]


def test_transcript_is_never_logged(client, caplog):
    secret = "my unique spoken phrase zebra-quartz-77 pay fine"
    with caplog.at_level(logging.DEBUG):
        signed_post(client, "/twilio/gather", {"CallSid": "CA11", "From": "+919800000011", "SpeechResult": secret})
    assert "zebra-quartz-77" not in caplog.text


async def test_no_demo_number_means_no_crash_and_nothing_sent(monkeypatch):
    from kavach.calls import screening
    monkeypatch.setattr(settings, "DEMO_USER_NUMBER", "")
    assert await screening.screen_transcript("CA1", "+919811111111", "customs fine") is None
    res = await screening.screen_hangup("CA2", "+919811111111")
    assert res.hung_up_without_reason and wa.OUTBOX == []
