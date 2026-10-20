import pytest

from kavach.analysis import pulse
from kavach.analysis.models import AnalysisResult, ScamType


def _result(level: str, scam_type: ScamType = ScamType.courier_customs) -> AnalysisResult:
    return AnalysisResult(request_id="r", risk_level=level, risk_score=80 if level == "high" else 10,
                          scam_type=scam_type, explanation_en="x", recommended_action="none")


def test_replay_alerts_only_the_coimbatore_wave_three_runs_in_a_row(pulse_db):
    # TF-IDF keeps the English and Tamil copies of the courier template as separate clusters
    # (e5 would join them), so the wave can surface as one alert per language.
    for _ in range(3):
        pulse.replay()
        alerts = pulse.alerts()
        assert alerts and {(a.district, a.scam_type, a.confidence) for a in alerts} == \
            {("Coimbatore", ScamType.courier_customs, "emerging")}
        assert all(a.report_count >= 5 and a.distinct_reporters >= 3 for a in alerts)
        assert len({a.cluster_id for a in alerts}) == len(alerts)


def test_unrelated_campaigns_with_same_type_and_district_stay_separate(pulse_db):
    customs = "Your parcel is held by customs with illegal items. Press 1 to talk to the customs officer"
    redelivery = "Courier delivery failed due to incomplete address. Pay a small redelivery fee at <URL>"
    for i in range(6):
        pulse.ingest(_result("high"), customs, "Erode", f"wa-a{i % 3}")
        pulse.ingest(_result("high"), redelivery, "Erode", f"wa-b{i % 3}")
    alerts = pulse.alerts()
    assert len(alerts) == 2                                  # not merged into one courier_customs alert
    assert all(a.scam_type == ScamType.courier_customs and a.district == "Erode" for a in alerts)
    assert {a.report_count for a in alerts} == {6}
    assert len({a.cluster_id for a in alerts}) == 2 and len({a.sample_text for a in alerts}) == 2


def test_reporter_id_is_stored_as_salted_hash(pulse_db, monkeypatch):
    import hashlib
    pulse.ingest(_result("high"), "Parcel held by customs, press 1", "Salem", "+919000011122")
    with pulse._connect() as conn:
        stored = conn.execute("SELECT reporter_hash FROM report").fetchone()[0]
    assert "9000011122" not in stored
    assert stored != hashlib.sha256(b"+919000011122").hexdigest()     # not a plain, guessable hash
    assert stored == pulse.reporter_key("+919000011122")
    monkeypatch.setattr(pulse.settings, "HASH_SALT", "another-test-salt-not-a-secret-02")
    assert pulse.reporter_key("+919000011122") != stored               # depends on the server salt


def test_report_without_reporter_is_not_stored(pulse_db):
    pulse.ingest(_result("high"), "Parcel held by customs, press 1", "Salem", "")
    with pulse._connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM report").fetchone()[0] == 0


def test_legit_messages_are_never_stored(pulse_db):
    pulse.ingest(_result("low", ScamType.not_scam), "Hi Amma, reached safely", "Coimbatore", "h1")
    assert pulse.alerts() == []
    with pulse._connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM report").fetchone()[0] == 0


def test_stored_text_has_no_personal_data(pulse_db):
    pulse.ingest(_result("high"), "Call 9000011122, pay Rs 5,000 to a.b@okfake at http://x.xyz/p", "coimbatore", "h1")
    with pulse._connect() as conn:
        text, district = conn.execute("SELECT normalized_text, district FROM report").fetchone()
    assert "9000011122" not in text and "a.b@okfake" not in text and "x.xyz" not in text
    assert district == "Coimbatore"


def test_five_reports_from_two_reporters_do_not_alert(pulse_db):
    for i in range(6):
        pulse.ingest(_result("high"), "Parcel held by customs, press 1 to talk to officer", "Salem", f"h{i % 2}")
    assert pulse.alerts() == []


def test_matching_news_item_confirms_the_alert(pulse_db):
    pulse.replay()
    with pulse._connect() as conn:
        conn.execute("CREATE TABLE news_item (id TEXT, url TEXT, title TEXT, published_at TEXT, "
                     "scam_type TEXT, region TEXT, summary TEXT)")
        conn.execute("INSERT INTO news_item VALUES ('n1','u','t', datetime('now'), 'courier_customs','TN','s')")
    assert pulse.alerts()[0].confidence == "confirmed"


def _e5_cached() -> bool:
    from pathlib import Path
    return (Path.home() / ".cache" / "huggingface" / "hub" / "models--intfloat--multilingual-e5-small").exists()


@pytest.mark.skipif(not _e5_cached(), reason="multilingual-e5-small not downloaded (PULSE_EMBEDDINGS=e5 is optional)")
def test_e5_joins_tamil_and_english_copies_into_one_wave(pulse_db, monkeypatch):
    monkeypatch.setattr(pulse.settings, "PULSE_EMBEDDINGS", "e5")
    pulse.replay()
    alerts = pulse.alerts()
    assert len(alerts) == 1
    a = alerts[0]
    assert (a.district, a.scam_type) == ("Coimbatore", ScamType.courier_customs)
    assert a.report_count == 24 and "English" in a.label and "Tamil" in a.label
