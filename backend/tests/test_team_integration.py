"""Person 1's WhatsApp layer calling the analysis engine through the team contract.

These use Person 1's real `kavach.contracts` and `kavach.flows.engine`, unchanged.
"""
import runpy
from pathlib import Path

import pytest

from kavach import contracts as team
from kavach.analysis import bridge
from kavach.analysis.models import EvidenceExtraction, InputType
from kavach.analysis.scam_check import analyze
from kavach.flows import engine

APKS = Path(__file__).resolve().parents[2] / "data" / "samples" / "apks"
KYC = "Dear SBI customer, your account will be blocked today. Update KYC at sbi-kyc-update.xyz and share the OTP"


async def test_team_request_returns_team_result():
    r = await analyze(team.AnalysisRequest(text=KYC, language="en", source="whatsapp", user_id="+919000000001"))
    assert isinstance(r, team.AnalysisResult)
    assert r.risk_level == team.RiskLevel.HIGH and r.scam_type == "kyc_update"
    assert r.red_flags and all(f.label and f.explanation for f in r.red_flags)
    assert r.recommended_action.startswith("Do not reply")
    assert r.links and r.links[0]["lookalike_of"] == "sbi.co.in"


async def test_person1_format_verdict_renders_engine_result():
    r = await analyze(team.AnalysisRequest(text=KYC))
    text = engine._format_verdict(r)
    assert text.startswith("Risk: HIGH") and "Fake look-alike website" in text and "Chakshu" in text


async def test_person1_handle_check_end_to_end(monkeypatch):
    sent = []

    async def capture(user_id, body, buttons, language):
        sent.append((user_id, body, buttons))

    monkeypatch.setattr(engine, "_reply_buttons", capture)
    msg = team.IncomingMessage(sender="+919000000001", message_id="m1", kind="text",
                               text="sir this is customs, your parcel has drugs, press 1")
    await engine._handle_check(msg, "en")
    [(to, body, buttons)] = sent
    assert to == "+919000000001" and body.startswith("Risk: ") and "Risk: LOW" not in body
    assert ("gh_start", "I already paid") in buttons


async def test_apk_from_whatsapp_document_is_scanned():
    runpy.run_path(str(APKS / "build_test_apks.py"), run_name="__main__")
    r = await analyze(team.AnalysisRequest(media_path=str(APKS / "rto_challan_test.apk"), media_type="document"))
    assert r.risk_level == team.RiskLevel.HIGH and r.scam_type == "malicious_apk"
    assert r.recommended_action.startswith("Do not install")


async def test_voice_note_without_transcript_is_unknown_not_safe():
    r = await analyze(team.AnalysisRequest(media_path="files/voice.ogg", media_type="audio/ogg"))
    assert r.risk_level == team.RiskLevel.UNKNOWN and "voice note" in r.explanation


@pytest.mark.parametrize("req, expected", [
    (team.AnalysisRequest(text="hello"), InputType.text),
    (team.AnalysisRequest(text="sbi-kyc-update.xyz/login"), InputType.url),
    (team.AnalysisRequest(media_path="files/a.jpg", media_type="image/jpeg"), InputType.image),
    (team.AnalysisRequest(media_path="files/x.apk", media_type="application/vnd.android.package-archive"),
     InputType.apk),
    (team.AnalysisRequest(text="press 1", source="call"), InputType.transcript),
])
def test_request_mapping(req, expected):
    assert bridge.to_engine(req).input_type == expected


def test_user_id_is_not_passed_to_the_engine():
    eng = bridge.to_engine(team.AnalysisRequest(text="hi", user_id="+919000000001"))
    assert "9000000001" not in eng.model_dump_json()


async def test_bait_verifier_through_bridge():
    r = await bridge.verify_bait(team.AnalysisRequest(
        text="verify PM Free Laptop Yojana! Register at pm-laptop-yojana.site and pay Rs 199 fee"))
    assert isinstance(r, team.AnalysisResult) and r.risk_level == team.RiskLevel.HIGH


def test_evidence_maps_to_person1_summary():
    s = bridge.to_evidence_summary(EvidenceExtraction(
        transaction_id="612345678901", amount="₹15,000", datetime="12 Oct 2026, 10:42 AM",
        payee_upi="ravi.kumar99@okfake", payee_name="Ravi Kumar", scammer_phone="9000000002",
        missing_fields=["bank_name"]))
    assert isinstance(s, team.EvidenceSummary)
    assert (s.transaction_id, s.transaction_time, s.scammer_number) == ("612345678901", "12 Oct 2026, 10:42 AM",
                                                                        "9000000002")
    assert s.additional_details == {"payee_name": "Ravi Kumar", "missing_fields": "bank_name"}
