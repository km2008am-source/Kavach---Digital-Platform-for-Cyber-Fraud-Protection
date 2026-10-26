"""Fixtures for the website API, simulator and Call Shield tests.

Each test gets its own SQLite file, a signed-Twilio helper, and an OUTBOX that records the alerts
Call Shield would send on the bot channel (no Telegram or WhatsApp request ever leaves the test).
"""
import pytest
from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator

from kavach.analysis import pulse
from kavach.api import errors, store
from kavach.calls import screening
from kavach.simulator import engine
from kavach.web_settings import settings

BASE = "https://kavach.test"
TOKEN = "test-token"
DEMO = "+919800000000"
OUTBOX: list[dict] = []


@pytest.fixture
def web_env(monkeypatch, tmp_path):
    db = str(tmp_path / "web.db")
    store.configure(db)
    pulse.configure(db)
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", TOKEN)
    monkeypatch.setattr(settings, "PUBLIC_BASE_URL", BASE)
    monkeypatch.setattr(settings, "DEMO_USER_NUMBER", DEMO)
    monkeypatch.setattr(settings, "DEMO_USER_LANG", "en")

    async def send_text(to, body):
        OUTBOX.append({"kind": "text", "to": to, "body": body})

    async def send_buttons(to, body, buttons):
        OUTBOX.append({"kind": "buttons", "to": to, "body": body[:1000], "buttons": [(i, t[:20]) for i, t in buttons[:3]]})

    monkeypatch.setattr(screening, "send_text", send_text)
    monkeypatch.setattr(screening, "send_buttons", send_buttons)
    OUTBOX.clear()
    engine._sessions.clear()
    errors._hits.clear()
    yield
    store.configure(None)
    pulse.configure(None)


@pytest.fixture
def client(web_env):
    from kavach.main import app
    with TestClient(app) as c:
        yield c


def signed_post(client, path: str, form: dict):
    """POST as Twilio would: compute X-Twilio-Signature for BASE + path."""
    sig = RequestValidator(TOKEN).compute_signature(BASE + path, form)
    return client.post(path, data=form, headers={"X-Twilio-Signature": sig})
