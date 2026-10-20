import os, tempfile

# Must be set before kavach is imported: the DB engine is created at import time.
_tmp = tempfile.mkdtemp(prefix="kavach-test-")
os.environ["DB_URL"] = f"sqlite:///{_tmp}/test.db"

import pytest
from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator

from kavach.config import settings
from kavach.main import app
from kavach.whatsapp import client as wa

BASE = "https://kavach.test"
TOKEN = "test-token"
DEMO = "+919800000000"


@pytest.fixture(autouse=True)
def cfg(monkeypatch):
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", TOKEN)
    monkeypatch.setattr(settings, "PUBLIC_BASE_URL", BASE)
    monkeypatch.setattr(settings, "DEMO_USER_NUMBER", DEMO)
    monkeypatch.setattr(settings, "DEMO_USER_LANG", "en")
    monkeypatch.setattr(settings, "LLM_BASE_URL", "")     # tests never reach a real LLM
    monkeypatch.setattr(settings, "LLM_API_KEY", "")
    wa.OUTBOX.clear()
    yield


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def signed_post(client, path: str, form: dict):
    """POST as Twilio would: compute X-Twilio-Signature for BASE + path."""
    sig = RequestValidator(TOKEN).compute_signature(BASE + path, form)
    return client.post(path, data=form, headers={"X-Twilio-Signature": sig})
