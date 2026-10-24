"""Vision fallback for screenshots when Tesseract is not installed."""
import base64
import io
import json

import httpx
import pytest
import respx
from PIL import Image

from kavach.analysis import ocr, scam_check
from kavach.analysis.settings import settings

HINDI_SMS = "प्रिय ग्राहक, आपका खाता आज ही ब्लॉक हो जाएगा। केवाईसी के लिए http://sbi-\nkyc-update.example पर तुरंत ओटीपी बताएं।"


@pytest.fixture
def shot(tmp_path):
    p = tmp_path / "shot.png"
    Image.new("RGB", (3000, 1000), "white").save(p)
    return str(p)


@pytest.fixture
def no_tesseract(monkeypatch):
    def missing(path):
        raise ocr.OCRUnavailable("tesseract not installed")
    monkeypatch.setattr(ocr, "_read_tesseract", missing)


@pytest.fixture
def vision_on(monkeypatch, llm_on):
    monkeypatch.setattr(settings, "LLM_API_KEY", "test-key-not-a-secret")
    monkeypatch.setattr(settings, "OCR_VISION_MODEL", "test-vision")
    return llm_on


@respx.mock
def test_vision_reads_hindi_and_rejoins_links(shot, no_tesseract, vision_on, llm_reply):
    route = respx.post(vision_on).mock(return_value=httpx.Response(200, json=llm_reply(HINDI_SMS)))
    text = ocr.read(shot)
    assert "http://sbi-kyc-update.example" in text and "ओटीपी बताएं" in text
    sent = json.loads(route.calls.last.request.content)
    assert sent["model"] == "test-vision"
    image = sent["messages"][0]["content"][1]["image_url"]["url"]
    with Image.open(io.BytesIO(base64.b64decode(image.split(",", 1)[1]))) as img:
        assert max(img.size) <= ocr.VISION_MAX_SIDE          # large screenshots are scaled down


def test_without_vision_model_ocr_stays_unavailable(shot, no_tesseract):
    assert not ocr.vision_enabled()
    with pytest.raises(ocr.OCRUnavailable):
        ocr.read(shot)


@respx.mock
def test_vision_error_is_reported_as_unavailable(shot, no_tesseract, vision_on):
    respx.post(vision_on).mock(return_value=httpx.Response(503))
    with pytest.raises(ocr.OCRUnavailable):
        ocr.read(shot)


@respx.mock
async def test_hindi_screenshot_gets_the_same_verdict_as_its_text(shot, no_tesseract, vision_on, llm_reply,
                                                                   request_factory, monkeypatch):
    respx.post(vision_on).mock(return_value=httpx.Response(200, json=llm_reply(HINDI_SMS)))
    monkeypatch.setattr(settings, "LLM_MODEL", "")             # verdict from rules only, LLM off
    r = await scam_check.analyze(request_factory("", input_type="image", file_path=shot, language="hi"))
    assert r.risk_level == "high" and {"otp_request", "kyc", "urgency"} <= {f.code for f in r.red_flags}
