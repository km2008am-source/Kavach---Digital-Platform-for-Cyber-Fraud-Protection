import asyncio, json, os
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from kavach.analysis import pulse
from kavach.api import analyze as analyze_mod, errors, news_fetch
from kavach.config import settings
from kavach.contracts import AnalysisResult, InputType, PulseAlert
from kavach.db import NewsItem, get_session, init_db
from kavach.main import app
from kavach.simulator import engine

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture(autouse=True)
def _reset(monkeypatch, tmp_path):
    init_db()
    engine._sessions.clear()
    errors._hits.clear()
    monkeypatch.setattr(analyze_mod, "FILES_DIR", str(tmp_path / "files"))
    monkeypatch.setattr(settings, "NEWS_FEEDS", [])
    monkeypatch.setattr(news_fetch, "DEMO_PATH", str(tmp_path / "no-demo.json"))
    with get_session() as db:
        for r in db.exec(select(NewsItem)).all():
            db.delete(r)
        db.commit()


def spy(monkeypatch):
    seen = []
    async def fake(req):
        seen.append({"req": req, "file_existed": bool(req.file_path and os.path.exists(req.file_path))})
        return AnalysisResult(request_id=req.request_id, risk_level="high", risk_score=90,
                              scam_type="kyc_update", explanation_en="x", recommended_action="report_chakshu")
    monkeypatch.setattr(analyze_mod, "analyze", fake)
    return seen


def assert_error(r, status, code):
    assert r.status_code == status, r.text
    body = r.json()
    assert set(body) == {"error", "message"} and body["error"] == code and body["message"]


# ---- error format --------------------------------------------------------------------------------
def test_unknown_api_path_uses_error_format(client):
    assert_error(client.get("/api/nope"), 404, "not_found")


def test_wrong_method_uses_error_format(client):
    # With web/dist built, the static app mounted at "/" answers first, so a wrong method is a 404 there
    # and a 405 otherwise. Either way the body must use the one error format.
    r = client.get("/api/sim/turn")
    assert r.status_code in (404, 405), r.text
    body = r.json()
    assert set(body) == {"error", "message"} and body["error"] in ("not_found", "method_not_allowed")


def test_validation_error_uses_error_format(client):
    assert_error(client.post("/api/sim/turn", json={"session_id": 5}), 422, "invalid_request")


def test_unhandled_error_hides_details(monkeypatch):
    async def boom(req): raise RuntimeError("secret internal detail /etc/passwd")
    monkeypatch.setattr(analyze_mod, "analyze", boom)
    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.post("/api/analyze", json={"text": "hello"})
    assert_error(r, 500, "server_error")
    assert "secret" not in r.text and "passwd" not in r.text


# ---- /api/analyze: JSON -------------------------------------------------------------------------------
def test_analyze_text_returns_contract_shape(client, monkeypatch):
    seen = spy(monkeypatch)
    r = client.post("/api/analyze", json={"text": "Your SBI account will be blocked, share OTP", "language": "ta"})
    assert r.status_code == 200
    AnalysisResult(**r.json())
    q = seen[0]["req"]
    assert q.channel == "web" and q.input_type == InputType.text and q.language == "ta"


@pytest.mark.parametrize("text,kind", [("https://sbi-kyc.xyz/login", InputType.url),
                                       ("www.example.com/a", InputType.url),
                                       ("click https://x.com now", InputType.text)])
def test_analyze_detects_url_vs_text(client, monkeypatch, text, kind):
    seen = spy(monkeypatch)
    client.post("/api/analyze", json={"text": text})
    assert seen[0]["req"].input_type == kind


@pytest.mark.parametrize("payload", [{}, {"text": "   "}, {"text": None}])
def test_analyze_empty_input(client, monkeypatch, payload):
    spy(monkeypatch)
    assert_error(client.post("/api/analyze", json=payload), 422, "empty_input")


def test_analyze_rejects_oversized_text_and_junk(client, monkeypatch):
    spy(monkeypatch)
    assert_error(client.post("/api/analyze", json={"text": "a" * 5001}), 422, "invalid_request")
    assert_error(client.post("/api/analyze", content=b"not json", headers={"content-type": "application/json"}), 422, "invalid_request")
    assert_error(client.post("/api/analyze", json=["a", "list"]), 422, "invalid_request")
    assert_error(client.post("/api/analyze", json={"text": "x", "language": "fr"}), 422, "invalid_request")


# ---- /api/analyze: files ------------------------------------------------------------------------------------
def test_image_upload_is_passed_by_path_and_deleted_after(client, monkeypatch, tmp_path):
    seen = spy(monkeypatch)
    r = client.post("/api/analyze", files={"file": ("shot.png", PNG, "image/png")}, data={"text": ""})
    assert r.status_code == 200
    q = seen[0]
    assert q["req"].input_type == InputType.image and q["file_existed"]
    assert not os.path.exists(q["req"].file_path)          # web uploads are not kept at all


def test_apk_upload(client, monkeypatch):
    seen = spy(monkeypatch)
    r = client.post("/api/analyze", files={"file": ("RTO Challan.apk", b"PK\x03\x04" + b"0" * 50,
                                                      "application/vnd.android.package-archive")})
    assert r.status_code == 200 and seen[0]["req"].input_type == InputType.apk
    assert not os.path.exists(seen[0]["req"].file_path)


def test_renamed_text_file_as_apk_still_goes_to_the_analyser(client, monkeypatch):
    seen = spy(monkeypatch)   # M2's scanner owns "could not read this file, do not install it"
    r = client.post("/api/analyze", files={"file": ("x.apk", b"just text", "application/octet-stream")})
    assert r.status_code == 200 and seen[0]["req"].input_type == InputType.apk


def test_fake_image_is_refused(client, monkeypatch):
    spy(monkeypatch)
    r = client.post("/api/analyze", files={"file": ("x.png", b"<html>not an image</html>", "image/png")})
    assert_error(r, 415, "unsupported_file")


@pytest.mark.parametrize("name", ["virus.exe", "doc.pdf", "noext", "a.png.exe"])
def test_other_file_types_are_refused(client, monkeypatch, name):
    spy(monkeypatch)
    assert_error(client.post("/api/analyze", files={"file": (name, PNG, "application/octet-stream")}), 415, "unsupported_file")


def test_client_file_name_is_never_used_on_disk(client, monkeypatch):
    seen = spy(monkeypatch)
    client.post("/api/analyze", files={"file": ("../../etc/evil.png", PNG, "image/png")})
    p = seen[0]["req"].file_path
    assert ".." not in p and "evil" not in p and p.startswith(analyze_mod.FILES_DIR) and p.endswith(".png")


def test_oversized_and_empty_files(client, monkeypatch):
    spy(monkeypatch)
    big = b"\x89PNG\r\n\x1a\n" + b"0" * (analyze_mod.MAX_FILE + 10)
    assert_error(client.post("/api/analyze", files={"file": ("big.png", big, "image/png")}), 413, "file_too_large")
    assert_error(client.post("/api/analyze", files={"file": ("e.png", b"", "image/png")}), 422, "empty_input")


def test_timeout_returns_504_and_still_deletes_the_file(client, monkeypatch):
    paths = []
    async def slow(req):
        paths.append(req.file_path)
        await asyncio.sleep(5)
    monkeypatch.setattr(analyze_mod, "analyze", slow)
    monkeypatch.setattr(analyze_mod, "TIMEOUT", 0.05)
    r = client.post("/api/analyze", files={"file": ("s.png", PNG, "image/png")})
    assert_error(r, 504, "analysis_timeout")
    assert paths and not os.path.exists(paths[0])


def test_rate_limit(client, monkeypatch):
    spy(monkeypatch)
    codes = [client.post("/api/analyze", json={"text": "hi"}).status_code for _ in range(31)]
    assert codes[:30] == [200] * 30 and codes[30] == 429
    assert_error(client.post("/api/analyze", json={"text": "hi"}), 429, "rate_limited")


# ---- /api/sim ----------------------------------------------------------------------------------------------------------
def test_sim_flow_over_http(client):
    r = client.post("/api/sim/start", json={"language": "en"})
    assert r.status_code == 200
    s = r.json()
    assert s["tactics"] == ["authority"] and s["max_turns"] == 8 and len(s["quiz"]) == 4
    assert "a" not in s["quiz"][0] and "answers" not in json.dumps(s["quiz"]).lower()
    sid = s["session_id"]
    assert client.post("/api/sim/quiz", json={"session_id": sid, "phase": "pre", "answers": ["yes"] * 4}).json()["score"] == 25
    t = client.post("/api/sim/turn", json={"session_id": sid, "user_message": "who is this"}).json()
    assert t["finished"] is False and t["tactics"] and 0 <= t["user_turn_score"] <= 10
    t = client.post("/api/sim/turn", json={"session_id": sid, "user_message": "I am hanging up and calling 1930"}).json()
    assert t["finished"] and t["final_score"] is not None and t["debrief"]
    assert client.post("/api/sim/quiz", json={"session_id": sid, "phase": "post", "answers": ["no", "no", "no", "yes"]}).json()["score"] == 100
    assert_error(client.post("/api/sim/turn", json={"session_id": sid, "user_message": "hello?"}), 409, "session_finished")


def test_sim_error_cases(client):
    assert_error(client.post("/api/sim/turn", json={"session_id": "nope", "user_message": "hi"}), 404, "session_not_found")
    assert_error(client.post("/api/sim/start", json={"language": "fr"}), 422, "invalid_request")
    sid = client.post("/api/sim/start", json={}).json()["session_id"]       # language defaults to en
    assert_error(client.post("/api/sim/turn", json={"session_id": sid, "user_message": "   "}), 422, "empty_input")
    assert_error(client.post("/api/sim/turn", json={"session_id": sid, "user_message": "a" * 501}), 422, "message_too_long")
    assert_error(client.post("/api/sim/quiz", json={"session_id": sid, "phase": "post", "answers": []}), 409, "session_not_finished")


# ---- /api/pulse -------------------------------------------------------------------------------------------------------------
def test_pulse_replay_is_closed_unless_demo_mode(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    assert_error(client.post("/api/pulse/replay"), 403, "replay_disabled")


def test_pulse_replay_then_alerts_match_the_contract(client, monkeypatch):
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    assert client.post("/api/pulse/replay").json() == {"ok": True, "demo_data": True}
    alerts = client.get("/api/pulse/alerts").json()
    assert alerts and [PulseAlert(**a) for a in alerts]
    assert_error(client.get("/api/pulse/alerts?hours=0"), 422, "invalid_request")


def test_pulse_accepts_async_replay_from_the_real_module(client, monkeypatch):
    called = []
    async def real_replay(): called.append(1)
    monkeypatch.setattr(pulse, "replay", real_replay)
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    assert client.post("/api/pulse/replay").status_code == 200 and called


# ---- news ------------------------------------------------------------------------------------------------------------------------
RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Digital arrest scam: retiree loses savings</title><link>https://example.com/a</link>
 <description>&lt;p&gt;Police warn of &lt;b&gt;fraud&lt;/b&gt; calls.&lt;/p&gt;</description>
 <pubDate>Mon, 19 Oct 2026 10:00:00 GMT</pubDate></item>
<item><title>Cricket final tonight</title><link>https://example.com/b</link><description>Sports</description></item>
<item><title>Phishing site pretends to be a bank</title><link>javascript:alert(1)</link><description>x</description></item>
<item><title>Cyber fraud ring busted</title><link>https://example.com/c</link><description>%s</description></item>
</channel></rss>""" % ("long " * 100)


def test_parse_entries_filters_cleans_and_blocks_bad_links():
    items = news_fetch.parse_entries(RSS)
    assert [i["url"] for i in items] == ["https://example.com/a", "https://example.com/c"]
    a, c = items
    assert a["summary"] == "Police warn of fraud calls." and a["published_at"].startswith("2026-10-19")
    assert len(c["summary"]) <= 240 and c["published_at"] is None


async def test_get_feed_survives_failures():
    ok = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=RSS.encode())))
    bad = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    assert len(await news_fetch._get_feed(ok, "https://feed.test/ok")) == 2
    assert await news_fetch._get_feed(bad, "https://feed.test/bad") == []
    def boom(r): raise httpx.ConnectError("blocked")
    dead = httpx.AsyncClient(transport=httpx.MockTransport(boom))
    assert await news_fetch._get_feed(dead, "https://feed.test/dead") == []


async def test_refresh_stores_tags_dedupes_and_never_raises(monkeypatch):
    monkeypatch.setattr(settings, "NEWS_FEEDS", ["https://feed.test/1", "https://feed.test/2"])
    async def fake_get(client, url): return news_fetch.parse_entries(RSS)
    monkeypatch.setattr(news_fetch, "_get_feed", fake_get)
    assert await news_fetch.refresh() == 2          # same two items from both feeds: stored once
    assert await news_fetch.refresh() == 2          # a second run adds nothing
    with get_session() as db:
        assert any(r.scam_type == "digital_arrest" for r in db.exec(select(NewsItem)).all())
    async def broken(client, url): raise RuntimeError("everything is on fire")
    monkeypatch.setattr(news_fetch, "_get_feed", broken)
    assert await news_fetch.refresh() >= 0          # must not raise


async def test_refresh_with_no_feeds_is_a_no_op():
    assert await news_fetch.refresh() == 0


def test_news_endpoint_prefers_db_then_marked_demo_then_empty(client, monkeypatch, tmp_path):
    assert client.get("/api/news").json() == []
    demo = tmp_path / "news.json"
    demo.write_text(json.dumps([{"url": "https://example.com/real", "title": "Real article", "summary": "s"},
                                {"url": "javascript:alert(1)", "title": "bad link"},
                                {"url": "https://example.com/notitle"}]))
    monkeypatch.setattr(news_fetch, "DEMO_PATH", str(demo))
    got = client.get("/api/news").json()
    assert [g["url"] for g in got] == ["https://example.com/real"] and got[0]["demo"] is True
    with get_session() as db:
        db.add(NewsItem(url="https://example.com/live", title="Live", scam_type="phishing_link"))
        db.add(NewsItem(url="javascript:evil()", title="never shown"))
        db.commit()
    got = client.get("/api/news").json()
    assert [g["url"] for g in got] == ["https://example.com/live"] and got[0]["demo"] is False


# ---- CORS ----------------------------------------------------------------------------------------------------------------------------
def test_cors_allows_only_the_web_origin(client):
    ok = client.options("/api/sim/start", headers={"Origin": "http://localhost:5173",
                                                    "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = client.options("/api/sim/start", headers={"Origin": "https://evil.example",
                                                     "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers
