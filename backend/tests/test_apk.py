import runpy
from pathlib import Path

import pytest

from kavach.analysis import apk
from kavach.analysis.scam_check import analyze
from kavach.analysis.models import ApkReport, ScamType

APKS = Path(__file__).resolve().parents[2] / "data" / "samples" / "apks"


@pytest.fixture(scope="module", autouse=True)
def test_apks():
    runpy.run_path(str(APKS / "build_test_apks.py"), run_name="__main__")


async def test_rto_challan_trojan_pattern_is_high(request_factory):
    r = await analyze(request_factory(input_type="apk", file_path=str(APKS / "rto_challan_test.apk")))
    assert r.risk_level == "high" and r.scam_type == ScamType.malicious_apk
    assert r.apk.dangerous_combo and r.apk.app_name == "RTO Challan"
    assert r.recommended_action == "do_not_install"
    assert {"apk_dangerous_combo", "apk_name_mismatch"} <= {f.code for f in r.red_flags}


async def test_clean_apk_is_medium_not_high(request_factory):
    r = await analyze(request_factory(input_type="apk", file_path=str(APKS / "clean_notes_test.apk")))
    assert r.risk_level == "medium" and not r.apk.dangerous_combo
    assert r.red_flags[0].code == "apk_unknown_source"


async def test_renamed_text_file_does_not_crash(request_factory):
    r = await analyze(request_factory(input_type="apk", file_path=str(APKS / "not_an_apk.apk")))
    assert r.risk_level == "high" and "Could not read this file" in r.explanation_en


async def test_missing_file_does_not_crash(request_factory):
    r = await analyze(request_factory(input_type="apk", file_path=str(APKS / "missing.apk")))
    assert r.red_flags[0].code == "apk_unreadable"


def test_judge_sms_only_with_lure_name_is_high():
    score, flags = apk.judge(ApkReport(sha256="0" * 64, app_name="PM Kisan Update",
                                       permissions=["android.permission.READ_SMS"]))
    assert score >= 85 and flags[1].code == "apk_name_mismatch"


def test_judge_virustotal_detection_dominates():
    score, flags = apk.judge(ApkReport(sha256="0" * 64, app_name="Notes", vt_malicious=12))
    assert score >= 95 and flags[0].code == "apk_virustotal"


async def test_oversized_apk_is_rejected_without_reading_it(request_factory, monkeypatch, tmp_path):
    big = tmp_path / "huge.apk"
    big.write_bytes(b"x" * 2048)
    monkeypatch.setattr(apk, "MAX_APK_BYTES", 1024)      # 2 KB file stands in for a >100 MB one
    opened = []
    real_open = open
    monkeypatch.setattr("builtins.open", lambda p, *a, **k: opened.append(str(p)) or real_open(p, *a, **k))
    monkeypatch.setattr(apk, "APK", lambda p: pytest.fail("androguard must not parse an oversized file"))
    r = await analyze(request_factory(input_type="apk", file_path=str(big)))
    assert str(big) not in opened                          # never opened: no hashing, no parsing
    assert r.risk_level == "high" and r.recommended_action == "do_not_install"
    assert r.apk is None and r.red_flags[0].code == "apk_unreadable"
