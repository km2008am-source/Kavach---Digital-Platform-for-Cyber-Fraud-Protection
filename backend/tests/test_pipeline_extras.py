"""Latency budget, DEMO_MODE cache and OCR screenshots."""
import asyncio
import runpy
import time
from pathlib import Path

import pytest

from kavach.analysis import links, ocr, scam_check
from kavach.analysis.settings import settings
from kavach.analysis.models import LinkCheck
from tests.conftest import load_jsonl

SHOTS = Path(__file__).resolve().parents[2] / "data" / "samples" / "screenshots"


async def test_links_and_llm_run_in_parallel(request_factory, monkeypatch):
    async def slow_links(urls):
        await asyncio.sleep(0.3)
        return [LinkCheck(url=u, domain=links.domain_of(u)) for u in urls]

    async def slow_llm(system, user, timeout=12):
        await asyncio.sleep(0.3)
        return {"scam_type": "kyc_update", "risk_score": 80}

    monkeypatch.setattr(links, "check_links", slow_links)
    monkeypatch.setattr(scam_check, "complete_json", slow_llm)
    t0 = time.perf_counter()
    r = await scam_check.analyze(request_factory("Update KYC at http://example-kyc.xyz/a"))
    assert time.perf_counter() - t0 < 0.55          # sequential would take at least 0.6 s
    assert r.confidence == "normal" and r.risk_score >= 80


async def test_llm_timeout_fits_whatsapp_budget(request_factory, monkeypatch):
    seen = {}

    async def spy(system, user, timeout=12):
        seen["timeout"] = timeout
        raise scam_check.LLMError("down")

    monkeypatch.setattr(scam_check, "complete_json", spy)
    await scam_check.analyze(request_factory("hello"))
    assert seen["timeout"] + 5 <= 12               # LLM ≤ 7 s in parallel with link sources ≤ 5 s


async def test_demo_mode_returns_cached_verdict(request_factory, monkeypatch):
    sample = load_jsonl("scams.jsonl")[0]["text"]
    cached = (await scam_check.analyze(request_factory(sample))).model_dump(mode="json")
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    monkeypatch.setattr(scam_check, "_demo_cache", lambda: {sample: {**cached, "explanation_en": "from cache"}})
    r = await scam_check.analyze(request_factory(sample, request_id="demo-1"))
    assert r.explanation_en == "from cache" and r.request_id == "demo-1"
    other = await scam_check.analyze(request_factory("a message not in the cache"))
    assert other.explanation_en != "from cache"


async def test_demo_mode_off_ignores_cache(request_factory, monkeypatch):
    monkeypatch.setattr(scam_check, "_demo_cache", lambda: {"hi": {"explanation_en": "from cache"}})
    r = await scam_check.analyze(request_factory("hi"))
    assert r.explanation_en != "from cache"


def _tesseract_available() -> bool:
    try:
        ocr._langs()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _tesseract_available(), reason="Tesseract OCR is not installed")
async def test_screenshot_verdict_matches_text_verdict(request_factory):
    runpy.run_path(str(SHOTS / "make_screenshots.py"), run_name="__main__")
    rows = {r["id"]: r for r in load_jsonl("scams.jsonl") + load_jsonl("legit.jsonl")}
    for shot in sorted(p for p in SHOTS.glob("*.png") if p.stem in rows):   # skip ta_* (browser-rendered)
        text_r = await scam_check.analyze(request_factory(rows[shot.stem]["text"]))
        img_r = await scam_check.analyze(request_factory(input_type="image", file_path=str(shot)))
        assert img_r.risk_level == text_r.risk_level, shot.stem


def test_wrapped_link_from_ocr_is_rejoined():
    raw = "Update your\nKYC now at http://sbi-kyc-\nupdate.xyz/login and share the OTP\nto continue."
    fixed = ocr.rejoin_wrapped_links(raw)
    assert "http://sbi-kyc-update.xyz/login" in fixed
    assert "OTP\nto continue" in fixed                 # ordinary line breaks are kept


def test_oversized_image_is_not_decoded(monkeypatch, tmp_path):
    from kavach.analysis import files
    big = tmp_path / "huge.png"
    big.write_bytes(b"x" * 4096)
    monkeypatch.setattr(files.settings, "MAX_FILE_BYTES", 1024)
    monkeypatch.setattr(ocr.Image, "open", lambda *a, **k: pytest.fail("oversized image must not be opened"))
    with pytest.raises(files.FileTooLarge):
        ocr.read(str(big))


def test_default_upload_limit_is_20_mb():
    from kavach.analysis.settings import Settings
    assert Settings(_env_file=None).MAX_FILE_BYTES == 20 * 1024 * 1024


def _tamil_ocr_available() -> bool:
    try:
        return "tam" in ocr._langs()
    except Exception:
        return False


@pytest.mark.skipif(not _tamil_ocr_available(), reason="Tesseract Tamil language pack is not installed")
async def test_tamil_screenshot_is_read_and_flagged(request_factory):
    # ta_s03.png is dataset message s03 rendered by a browser (correct Tamil shaping; Pillow
    # without raqm draws Tamil vowel signs in the wrong order, so it cannot make this fixture).
    shot = SHOTS / "ta_s03.png"
    text = ocr.read(str(shot))
    assert "கைது" in text and "‌" not in text            # arrest; invisible joiners stripped
    r = await scam_check.analyze(request_factory(input_type="image", file_path=str(shot)))
    assert r.risk_level == "high" and "threat_arrest" in {f.code for f in r.red_flags}


def test_invisible_joiners_do_not_hide_keywords():
    from kavach.analysis import rules
    _, codes = rules.rule_flags("நீங்கள் டிஜிட்டல்‌ கை‌து செய்யப்பட்டுள்ளீர்கள்")
    assert "threat_arrest" in codes
