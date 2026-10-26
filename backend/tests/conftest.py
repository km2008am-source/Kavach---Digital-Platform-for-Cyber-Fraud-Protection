"""Shared fixtures. Unit tests never touch the network: every external source is off or mocked."""

# Website API, simulator and Call Shield fixtures (web_env, client).
pytest_plugins = ["tests.web_support"]
import json
from pathlib import Path

import pytest

from kavach.analysis import blocklist, links, pulse
from kavach.analysis.settings import settings
from kavach.analysis.models import AnalysisRequest

SAMPLES = Path(__file__).resolve().parents[2] / "data" / "samples"
LLM_URL = "https://llm.test/v1"


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(settings, "NETWORK_CHECKS", False)
    monkeypatch.setattr(settings, "LLM_BASE_URL", "")
    monkeypatch.setattr(settings, "LLM_MODEL", "")
    monkeypatch.setattr(settings, "PULSE_EMBEDDINGS", "tfidf")
    monkeypatch.setattr(settings, "HASH_SALT", "test-only-salt-not-a-secret-0001")
    monkeypatch.setattr(settings, "BLOCKLIST_PATH", str(Path(__file__).parent / "no-blocklist-in-tests.txt"))
    blocklist.hosts.cache_clear()
    links._cache.clear()


@pytest.fixture
def llm_on(monkeypatch):
    """Configure a fake LLM endpoint; tests mock it with respx."""
    monkeypatch.setattr(settings, "LLM_BASE_URL", LLM_URL)
    monkeypatch.setattr(settings, "LLM_MODEL", "test-model")
    return f"{LLM_URL}/chat/completions"


@pytest.fixture
def llm_reply():
    def _factory(content: dict | str) -> dict:
        body = content if isinstance(content, str) else json.dumps(content)
        return {"choices": [{"message": {"content": body}}]}
    return _factory


@pytest.fixture
def request_factory():
    def _factory(text: str = "", input_type: str = "text", **overrides) -> AnalysisRequest:
        return AnalysisRequest(request_id=overrides.pop("request_id", "t1"), channel="web",
                               input_type=input_type, text=text, **overrides)
    return _factory


@pytest.fixture
def pulse_db(tmp_path):
    pulse.configure(str(tmp_path / "pulse.db"))
    yield
    pulse.configure(None)


def load_jsonl(name: str) -> list[dict]:
    return [json.loads(l) for l in (SAMPLES / name).read_text("utf-8").splitlines() if l.strip()]
