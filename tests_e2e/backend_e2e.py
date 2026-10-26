"""End-to-end check of the Kavach backend: Telegram bot flows, website API and Call Shield.

Telegram's servers are replaced by a local fake (respx): the bot's replies, documents and audio are
captured instead of sent, so no real bot token is needed. Everything else (LLM, link checks, vision OCR,
Whisper) runs for real with the settings in backend/.env.

    cd backend
    python -m pip install -e ".[test,voice]"
    python ../tests_e2e/backend_e2e.py

Prints one PASS/FAIL line per check and a summary. Needs internet for the LLM and text-to-speech.
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
TMP = Path(tempfile.mkdtemp(prefix="kavach-e2e-"))
TOKEN, SECRET, CHAT, ALERT_CHAT = "TESTTOKEN", "sekret-123", 1001, "555000111"
os.environ.update({
    "WHATSAPP_PROVIDER": "telegram", "TELEGRAM_BOT_TOKEN": TOKEN, "TELEGRAM_WEBHOOK_SECRET": SECRET,
    "DATABASE_PATH": str(TMP / "kavach.db"), "FILES_DIR": str(TMP / "files"), "DRY_RUN": "0",
    "DEMO_MODE": "1", "DEMO_USER_NUMBER": ALERT_CHAT, "PUBLIC_BASE_URL": "https://kavach.test",
    "TWILIO_AUTH_TOKEN": "twilio-test-token", "HASH_SALT": "e2e-test-salt-0123456789abcdef",
})
sys.path.insert(0, os.getcwd())          # run from backend/

import httpx  # noqa: E402
import respx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from twilio.request_validator import RequestValidator  # noqa: E402

from kavach.main import app  # noqa: E402

ROOT = Path(os.getcwd()).parent
FILES = {
    "shot1": (ROOT / "data/samples/screenshots/hi_kyc_sms.png").read_bytes(),
    "receipt1": (ROOT / "data/samples/receipts/r01.png").read_bytes(),
    "apk1": (ROOT / "data/samples/apks/rto_challan_test.apk").read_bytes(),
}
from gtts import gTTS  # noqa: E402
voice_path = TMP / "voice.mp3"
gTTS("Hello, this is the customs office. Your parcel has drugs. Pay a fine now or you will be arrested.",
     lang="en").save(str(voice_path))
FILES["voice1"] = voice_path.read_bytes()

SENT: list[dict] = []          # every bot -> Telegram call


def _record(method):
    def handler(request: httpx.Request):
        entry = {"method": method}
        ctype = request.headers.get("content-type", "")
        if "json" in ctype:
            entry.update(json.loads(request.content))
        else:
            entry["bytes"] = len(request.content)
            entry["has_pdf"] = b"%PDF" in request.content
        SENT.append(entry)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": len(SENT)}})
    return handler


def _get_file(request: httpx.Request):
    fid = request.url.params.get("file_id") or json.loads(request.content or b"{}").get("file_id")
    return httpx.Response(200, json={"ok": True, "result": {"file_path": f"files/{fid}"}})


def _download(request: httpx.Request):
    fid = request.url.path.rsplit("/", 1)[-1]
    return httpx.Response(200, content=FILES[fid])


router = respx.mock(assert_all_called=False, assert_all_mocked=False)
base = f"https://api.telegram.org/bot{TOKEN}"
for m in ("sendMessage", "sendDocument", "sendAudio", "sendVoice", "sendChatAction"):
    router.post(f"{base}/{m}").mock(side_effect=_record(m))
router.route(url__regex=rf"{base}/getFile.*").mock(side_effect=_get_file)
router.route(url__regex=rf"https://api.telegram.org/file/bot{TOKEN}/files/.*").mock(side_effect=_download)
router.route().pass_through()

results: list[tuple[str, bool, str]] = []
mid = [100]


def check(name: str, ok: bool, detail: str = ""):
    results.append((name, ok, detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  | {detail}" if detail else ""))


def send(client, **message):
    mid[0] += 1
    before = len(SENT)
    payload = {"update_id": mid[0], "message": {"message_id": mid[0], "date": int(time.time()),
                                                 "chat": {"id": CHAT, "type": "private"}, **message}}
    r = client.post("/webhook/telegram", json=payload, headers={"X-Telegram-Bot-Api-Secret-Token": SECRET})
    new = SENT[before:]
    texts = " || ".join(e.get("text", "") for e in new if e["method"] == "sendMessage")
    return r, new, texts


def short(t, n=220):
    return t.replace("\n", " ")[:n]


with router, TestClient(app) as client:
    # ---------- security ----------
    r = client.post("/webhook/telegram", json={"update_id": 1}, headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"})
    check("Telegram webhook rejects a wrong secret", r.status_code == 403, f"HTTP {r.status_code}")

    # ---------- bot: menu ----------
    r, new, t = send(client, text="/start")
    check("Bot /start shows the menu", r.status_code == 200 and bool(t), short(t))

    # ---------- bot: text checks ----------
    r, new, t = send(client, text="Dear customer, your SBI account will be blocked today. Update KYC at "
                                   "http://sbi-kyc-update.xyz/login and share the OTP you receive.")
    check("Bot checks an English scam text", "high" in t.lower() or "risk" in t.lower(), short(t))

    r, new, t = send(client, text="आपका एसबीआई खाता आज ही ब्लॉक हो जाएगा। केवाईसी के लिए तुरंत अपना ओटीपी बताएं।")
    check("Bot checks a Hindi scam text and replies in Hindi", any("ऀ" <= ch <= "ॿ" for ch in t), short(t))

    r, new, t = send(client, text="http://sbi-kyc-update.xyz/login")
    check("Bot checks a bare link", bool(t), short(t))

    r, new, t = send(client, text="Hi Ravi, the team meeting is moved to 4 pm tomorrow in room 2.")
    check("Bot does not alarm on a genuine message", bool(t) and "high risk" not in t.lower(), short(t))

    # ---------- bot: screenshot ----------
    r, new, t = send(client, photo=[{"file_id": "shot1", "file_size": 5000, "width": 540, "height": 300}])
    check("Bot reads a Hindi screenshot and gives a verdict", bool(t) and ("high" in t.lower() or "risk" in t.lower()), short(t))

    # ---------- bot: APK ----------
    r, new, t = send(client, document={"file_id": "apk1", "file_name": "rto_challan.apk",
                                       "mime_type": "application/vnd.android.package-archive"})
    check("Bot scans an APK file", bool(t) and ("install" in t.lower() or "high" in t.lower()), short(t))

    # ---------- bot: voice note in, spoken reply out ----------
    r, new, t = send(client, voice={"file_id": "voice1", "mime_type": "audio/mpeg", "duration": 6})
    audio = [e for e in new if e["method"] in ("sendAudio", "sendVoice")]
    check("Bot transcribes a voice note and checks it", bool(t) and "couldn" not in t.lower() and "risk" in t.lower(), short(t))
    check("Bot replies to a voice note with audio", bool(audio), f"{len(audio)} audio reply(s)")

    # ---------- bot: Scam Bait ----------
    r, new, t = send(client, text="verify PM Free Laptop Yojana 2026: register at pm-free-laptop-yojana.xyz "
                                   "and pay Rs 499 fee. Share with 10 groups.")
    check("Bot verifies a fake scheme (Scam Bait)", bool(t) and ("pib" in t.lower() or "risk" in t.lower()), short(t))

    # ---------- bot: Pulse opt-in ----------
    r, new, t = send(client, text="district Coimbatore")
    check("Bot saves a Pulse district", bool(t), short(t))
    import sqlite3
    db = sqlite3.connect(TMP / "kavach.db")
    before = db.execute("SELECT COUNT(*) FROM report").fetchone()[0] if db.execute(
        "SELECT name FROM sqlite_master WHERE name='report'").fetchone() else 0
    send(client, text="Your parcel is held by customs with illegal items. Press 1 to speak to the officer or "
                      "a police case will be filed. Pay the fine today.")
    after = db.execute("SELECT COUNT(*) FROM report").fetchone()[0]
    check("A risky report from an opted-in user reaches Scam Pulse", after == before + 1, f"{before} -> {after}")

    # ---------- bot: Golden Hour, end to end ----------
    r, new, t = send(client, text="I lost money")
    check("Lost-money flow starts (Golden Hour)", "1930" in t, short(t))
    r, new, t = send(client, photo=[{"file_id": "receipt1", "file_size": 9000}])
    check("Golden Hour accepts a payment screenshot", bool(t), short(t))
    r, new, t = send(client, text="Done")
    check("Golden Hour asks for the transaction ID", bool(t), short(t))
    for answer in ("UTR612345678901", "Rs 4,999", "26 Oct 2026 10:15", "refund.help@paytmx", "9876543210"):
        r, new, t = send(client, text=answer)
    check("Golden Hour asks for the bank after the details", "bank" in t.lower(), short(t))
    r, new, t = send(client, text="SBI")
    check("Golden Hour gives the bank's fraud steps", "1930" in t, short(t))
    r, new, t = send(client, text="ACK1234567")
    docs = [e for e in new if e["method"] == "sendDocument"]
    check("Golden Hour sends the evidence PDF on Telegram", bool(docs) and docs[0].get("has_pdf"),
          f"{len(docs)} document(s), pdf={docs[0].get('has_pdf') if docs else None}")

    # ---------- website API ----------
    r = client.post("/api/analyze", json={"text": "Your electricity will be cut tonight. Call 9876543210 now.",
                                          "language": "en"})
    check("Website: Check a message gives a real verdict", r.status_code == 200 and "risk_level" in r.json(),
          f"{r.status_code} {r.json().get('risk_level')}")
    r = client.post("/api/analyze", files={"file": ("shot.png", FILES["shot1"], "image/png")}, data={"language": "hi"})
    check("Website: screenshot upload is analysed", r.status_code == 200, f"{r.status_code} {r.json().get('risk_level')}")
    r = client.post("/api/analyze", files={"file": ("app.apk", FILES["apk1"], "application/vnd.android.package-archive")})
    check("Website: APK upload is analysed", r.status_code == 200 and r.json().get("apk"), f"{r.json().get('risk_level')}")
    s = client.post("/api/sim/start", json={"language": "en"}).json()
    ok_q = client.post("/api/sim/quiz", json={"session_id": s["session_id"], "phase": "pre", "answers": ["no"] * 4}).status_code == 200
    tr = client.post("/api/sim/turn", json={"session_id": s["session_id"], "user_message": "I will hang up and call 1930"}).json()
    ok_post = client.post("/api/sim/quiz", json={"session_id": s["session_id"], "phase": "post", "answers": ["no", "no", "no", "yes"]}).status_code == 200
    check("Website: Training simulator runs a full call", ok_q and tr.get("finished") and tr.get("final_score") is not None and ok_post,
          f"final score {tr.get('final_score')}")
    check("Website: Pulse replay starts", client.post("/api/pulse/replay").json().get("ok") is True)
    alerts = client.get("/api/pulse/alerts").json()
    check("Website: Pulse returns alerts", isinstance(alerts, list) and len(alerts) > 0, f"{len(alerts)} alert(s)")
    news = client.get("/api/news")
    check("Website: News returns articles", news.status_code == 200 and len(news.json()) > 0, f"{len(news.json())} item(s)")
    svc = client.get("/api/services")
    check("Website: Get help returns services", svc.status_code == 200 and len(svc.json()) > 0, f"{len(svc.json())} service(s)")

    # ---------- Call Shield ----------
    def signed(path, form):
        sig = RequestValidator("twilio-test-token").compute_signature("https://kavach.test" + path, form)
        return client.post(path, data=form, headers={"X-Twilio-Signature": sig})

    check("Call Shield refuses unsigned requests", client.post("/twilio/voice", data={}).status_code == 403)
    v = signed("/twilio/voice", {"CallSid": "CA1", "From": "+919812345678"})
    check("Call Shield answers with a screening prompt", v.status_code == 200 and "<Gather" in v.text)
    before = len(SENT)
    g = signed("/twilio/gather", {"CallSid": "CA1", "From": "+919812345678",
                                   "SpeechResult": "I am calling from SBI, your account is blocked, tell me the OTP now"})
    alert = [e for e in SENT[before:] if e["method"] == "sendMessage"]
    check("Call Shield alerts the user on Telegram", g.status_code == 200 and bool(alert) and alert[0].get("chat_id") == ALERT_CHAT,
          short(alert[0]["text"]) if alert else "no alert")
    before = len(SENT)
    signed("/twilio/status", {"CallSid": "CA2", "From": "+919800011122", "CallStatus": "completed"})
    hang = [e for e in SENT[before:] if e["method"] == "sendMessage"]
    check("Call Shield alerts when a caller hangs up without a reason", bool(hang), short(hang[0]["text"]) if hang else "")

failed = [n for n, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)} of {len(results)} checks passed")
for n in failed:
    print("  FAILED:", n)

sys.exit(1 if failed else 0)
