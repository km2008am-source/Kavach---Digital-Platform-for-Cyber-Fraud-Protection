"""APK Scanner: judges an Android app file WITHOUT running it.

Static checks only: SHA-256, VirusTotal hash lookup (never upload), manifest permissions,
the SMS + accessibility/overlay combination used by OTP-stealing banking trojans, and a
claim check (an "RTO Challan" or "bank" app has no reason to read your SMS).
"""
import asyncio
import hashlib
import time
from pathlib import Path

import httpx

from kavach.analysis.settings import settings
from kavach.analysis.models import AnalysisRequest, AnalysisResult, ApkReport, RedFlag, ScamType

try:
    from loguru import logger as _loguru                   # androguard 4.x logs every parse step
    _loguru.disable("androguard")
except ImportError:
    pass
try:
    from androguard.core.apk import APK                    # androguard 4.x
except ImportError:                                        # pragma: no cover
    from androguard.core.bytecodes.apk import APK          # androguard 3.x

SMS = {"android.permission.READ_SMS", "android.permission.RECEIVE_SMS"}
OVERLAY = "android.permission.SYSTEM_ALERT_WINDOW"
RISKY_EXTRA = {"android.permission.READ_CONTACTS", "android.permission.CALL_PHONE",
               "android.permission.REQUEST_INSTALL_PACKAGES", "android.permission.READ_CALL_LOG"}
# App names scammers use for fake APKs sent over WhatsApp.
LURE_WORDS = ["rto", "challan", "pm kisan", "kisan", "bank", "invitation", "wedding", "kyc", "aadhaar",
              "electricity", "bill", "loan", "customer support", "income tax", "refund", "sbi", "yono"]
MAX_APK_BYTES = 100 * 1024 * 1024


class ApkParseError(Exception):
    pass


class ApkTooLarge(ApkParseError):
    pass


def check_size(path: str) -> None:
    """Reject oversized files from their size on disk, before reading a single byte."""
    if Path(path).stat().st_size > MAX_APK_BYTES:
        raise ApkTooLarge(f"larger than {MAX_APK_BYTES // (1024 * 1024)} MB")


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def inspect(path: str) -> ApkReport:
    check_size(path)
    sha = sha256_of(path)
    try:
        a = APK(path)
        perms = set(a.get_permissions())
        manifest = a.get_android_manifest_axml().get_xml().decode(errors="ignore")
        package, app_name = a.get_package(), a.get_app_name()
    except Exception as e:                                 # not a zip, no manifest, corrupt AXML ...
        raise ApkParseError(type(e).__name__) from e
    if not package:
        raise ApkParseError("no package name in manifest")
    accessibility = "android.accessibilityservice.AccessibilityService" in manifest \
        or "BIND_ACCESSIBILITY_SERVICE" in manifest
    combo = bool(perms & SMS) and (accessibility or OVERLAY in perms)
    return ApkReport(sha256=sha, package=package, app_name=app_name or None,
                     permissions=sorted(perms), dangerous_combo=combo)


async def vt_file(sha256: str) -> int | None:
    if not (settings.NETWORK_CHECKS and settings.VT_API_KEY):
        return None
    try:
        async with httpx.AsyncClient(timeout=6) as c:
            r = await c.get(f"https://www.virustotal.com/api/v3/files/{sha256}",
                            headers={"x-apikey": settings.VT_API_KEY})
        if r.status_code != 200:
            return None                                    # 404 = hash never seen
        return int(r.json()["data"]["attributes"]["last_analysis_stats"]["malicious"])
    except Exception:
        return None


def judge(report: ApkReport) -> tuple[int, list[RedFlag]]:
    """Score an ApkReport. Pure function: easy to test without APK files."""
    perms = set(report.permissions)
    name = f"{report.app_name or ''} {report.package or ''}".lower()
    lure = any(w in name for w in LURE_WORDS)
    score = 40                                             # any APK from an unknown sender is at least medium
    flags = [RedFlag(code="apk_unknown_source",
                     label_en="Apps sent on WhatsApp are not checked by Google. Install apps only from the Play Store.")]
    if report.dangerous_combo:
        score = max(score, 90)
        flags.insert(0, RedFlag(code="apk_dangerous_combo",
                                label_en="This app can read your SMS and control your screen. "
                                         "That is how OTP-stealing apps empty bank accounts."))
    elif perms & SMS:
        score = max(score, 70)
        flags.insert(0, RedFlag(code="apk_sms_permission",
                                label_en="This app wants to read your SMS, where your bank OTPs arrive."))
    if lure and perms & SMS:
        score = max(score, 85)
        flags.insert(1, RedFlag(code="apk_name_mismatch",
                                label_en=f"An app called '{report.app_name}' has no reason to read your SMS."))
    if perms & RISKY_EXTRA:
        score = min(100, score + 10)
    if report.vt_malicious:
        score = max(score, 95)
        flags.insert(0, RedFlag(code="apk_virustotal",
                                label_en=f"{report.vt_malicious} antivirus engines already flag this file as malware."))
    return score, flags[:4]


async def analyze_apk(req: AnalysisRequest) -> AnalysisResult:
    t0 = time.perf_counter()
    try:
        report = await asyncio.to_thread(inspect, req.file_path or "")
    except (ApkParseError, OSError) as e:
        sha = None
        if not isinstance(e, ApkTooLarge):                 # never read an oversized file just to hash it
            try:
                sha = sha256_of(req.file_path or "")
            except OSError:
                pass
        return AnalysisResult(
            request_id=req.request_id, risk_level="high", risk_score=80, scam_type=ScamType.malicious_apk,
            red_flags=[RedFlag(code="apk_unreadable", label_en="Could not read this file. Do not install it.")],
            explanation_en="Could not read this file. Do not install it. Real apps come from the Play Store.",
            recommended_action="do_not_install", apk=ApkReport(sha256=sha) if sha else None,
            latency_ms=int((time.perf_counter() - t0) * 1000))
    report.vt_malicious = await vt_file(report.sha256)
    score, flags = judge(report)
    level = "high" if score >= 70 else "medium"
    if level == "high":
        explanation = (f"Do not install '{report.app_name or 'this app'}'. It asks for permissions that let it "
                       "steal OTPs from your SMS. Delete the file.")
    else:
        explanation = ("We found no dangerous permissions, but apps sent on WhatsApp are risky. "
                       "Install apps only from the Play Store.")
    return AnalysisResult(
        request_id=req.request_id, risk_level=level, risk_score=score,
        scam_type=ScamType.malicious_apk if level == "high" else ScamType.unknown,
        red_flags=flags, explanation_en=explanation, recommended_action="do_not_install",
        apk=report, latency_ms=int((time.perf_counter() - t0) * 1000))
