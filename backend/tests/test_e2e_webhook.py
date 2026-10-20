"""Local end-to-end run: Meta webhook JSON -> Person 1's FastAPI app -> engine -> analysis -> reply.

Uses Person 1's real `kavach.main.app` in DRY_RUN mode (outgoing WhatsApp messages are printed,
not sent) with a temporary SQLite file. Only Meta's media download is replaced, because it
needs Meta's servers. This covers E2E-1/E2E-3 and integration points I1/I2 without phones.
"""
import dataclasses
import runpy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from kavach import config as team_config
from kavach import db
from kavach.flows import engine
from kavach.whatsapp import client as wa_client

APKS = Path(__file__).resolve().parents[2] / "data" / "samples" / "apks"
SENDER = "919000000001"                                    # fake number, Meta's format (no "+")


@pytest.fixture
def app_client(monkeypatch, tmp_path):
    test_settings = dataclasses.replace(team_config.settings, database_path=tmp_path / "kavach.db",
                                        files_dir=tmp_path / "files", dry_run=True)
    for module in (db, wa_client):
        monkeypatch.setattr(module, "settings", test_settings)

    async def no_translate(text, source="en", target="en"):
        return text                                        # keep the test offline

    monkeypatch.setattr(engine, "translate", no_translate)
    from kavach.main import app
    with TestClient(app) as c:
        yield c


def _webhook(message: dict) -> dict:
    return {"object": "whatsapp_business_account",
            "entry": [{"id": "1", "changes": [{"field": "messages", "value": {
                "messaging_product": "whatsapp", "messages": [message]}}]}]}


def _text(msg_id: str, body: str) -> dict:
    return {"from": SENDER, "id": msg_id, "timestamp": "1760000000", "type": "text", "text": {"body": body}}


def test_kyc_sms_gets_high_risk_reply_with_link_warning(app_client, capsys):
    body = "Dear SBI customer, your account will be blocked today. Update KYC at sbi-kyc-update.xyz and share the OTP"
    r = app_client.post("/webhook/whatsapp", json=_webhook(_text("wamid.e2e1", body)))
    assert r.status_code == 200 and r.json() == {"ok": True}
    out = capsys.readouterr().out
    assert "[WHATSAPP DRY RUN]" in out and "Risk: HIGH" in out
    assert "Fake look-alike website" in out and "I already paid" in out


def test_demo_customs_message_is_not_low(app_client, capsys):
    app_client.post("/webhook/whatsapp",
                    json=_webhook(_text("wamid.e2e2", "sir this is customs, your parcel has drugs, press 1")))
    out = capsys.readouterr().out
    assert "Risk: " in out and "Risk: LOW" not in out


def test_rto_challan_apk_document_is_scanned(app_client, capsys, monkeypatch):
    runpy.run_path(str(APKS / "build_test_apks.py"), run_name="__main__")

    async def fake_download(media_id, filename=None):
        return APKS / "rto_challan_test.apk"              # stands in for Meta's media download

    monkeypatch.setattr(engine, "download_media", fake_download)
    msg = {"from": SENDER, "id": "wamid.e2e3", "timestamp": "1760000000", "type": "document",
           "document": {"id": "media-1", "filename": "RTO_Challan.apk",
                        "mime_type": "application/vnd.android.package-archive"}}
    app_client.post("/webhook/whatsapp", json=_webhook(msg))
    out = capsys.readouterr().out
    assert "Risk: HIGH" in out and "Do not install" in out


def test_duplicate_delivery_gets_one_reply(app_client, capsys):
    payload = _webhook(_text("wamid.e2e4", "You have won a lottery, pay the processing fee of Rs 5,000 today"))
    app_client.post("/webhook/whatsapp", json=payload)
    app_client.post("/webhook/whatsapp", json=payload)
    assert capsys.readouterr().out.count("Risk: ") == 1
