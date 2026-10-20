from hypothesis import given, strategies as st

from kavach.analysis import rules
from kavach.analysis.pulse import normalize
from kavach.analysis.models import ScamType
from tests.conftest import load_jsonl


def test_guide_example_flags_otp_urgency_kyc():
    score, codes = rules.rule_flags("Your SBI account will be blocked today. Share OTP to continue KYC")
    assert {"otp_request", "urgency", "kyc"} <= set(codes)
    assert score >= 60


def test_bank_otp_alert_is_not_an_otp_request():
    score, codes = rules.rule_flags("123456 is your OTP for login. Do not share it with anyone.")
    assert "otp_request" not in codes and score == 0


def test_english_keywords_match_whole_words_only():
    _, codes = rules.rule_flags("Your Paytm recharge was successful")    # "pay" must not fire on "Paytm"
    assert "payment_request" not in codes


def test_tamil_keyword_matches_with_suffix():
    _, codes = rules.rule_flags("நீங்கள் டிஜிட்டல் கைது செய்யப்பட்டுள்ளீர்கள்")
    assert "threat_arrest" in codes


def test_entities_extracted():
    ents = rules.extract_entities("Call +91 9000011122 or pay ₹1,500 to refund.help@paytmx at http://x-pay.xyz/a.")
    assert ents["phones"] == ["+91 9000011122"]
    assert ents["upi_ids"] == ["refund.help@paytmx"]
    assert ents["amounts"] == ["₹1,500"]
    assert ents["urls"] == ["http://x-pay.xyz/a"]


def test_email_is_not_a_upi_id():
    assert rules.extract_entities("mail me at ravi@gmail.com")["upi_ids"] == []


def test_upi_reference_is_not_a_phone_number():
    assert rules.extract_entities("UPI Ref 612345678901")["phones"] == []


def test_dataset_loads_with_expected_shape():
    scams, legit = load_jsonl("scams.jsonl"), load_jsonl("legit.jsonl")
    assert len(scams) == 40 and len(legit) == 20
    assert len({s["scam_type"] for s in scams}) >= 6
    assert {"en", "ta", "hi"} <= {s["language"] for s in scams}
    for row in scams + legit:
        ScamType(row["scam_type"])


# ---- property-based: Pulse normalisation must never leak personal data ----

phones = st.from_regex(r"\A(\+91 )?[6-9][0-9]{9}\Z")
upis = st.from_regex(r"\A[a-z][a-z0-9.]{2,10}@[a-z]{3,8}\Z")
filler = st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Zs")), max_size=30)


@given(prefix=filler, phone=phones, upi=upis, suffix=filler)
def test_normalize_removes_phone_and_upi(prefix, phone, upi, suffix):
    out = normalize(f"{prefix} call {phone} pay {upi} {suffix}")
    assert phone.replace("+91 ", "") not in out
    assert upi not in out


@given(st.text(max_size=200))
def test_normalize_is_idempotent(text):
    once = normalize(text)
    assert normalize(once) == once
