import httpx
import respx

from kavach.analysis.bait import verify
from kavach.analysis.news_tagger import tag
from kavach.analysis.models import ScamType


async def test_fake_free_laptop_scheme_is_flagged(request_factory):
    r = await verify(request_factory("verify PM Free Laptop Yojana 2026! Register now at http://pm-laptop-yojana.site "
                                     "with Aadhaar and pay Rs 199 fee. Share with 10 groups."))
    assert r.risk_level == "high" and r.scam_type == ScamType.fake_scheme
    assert "factcheck.pib.gov.in" in r.explanation_en
    assert r.recommended_action == "verify_official"


async def test_lookalike_news_site_is_phishing(request_factory):
    r = await verify(request_factory("Breaking news: read full story at http://thehindu-breaking.xyz/story click now"))
    assert r.scam_type == ScamType.phishing_link and r.risk_level == "high"


async def test_plain_news_without_asks_is_low_and_not_called_fake(request_factory):
    r = await verify(request_factory("The state government opened a new bus stand in Coimbatore today."))
    assert r.risk_level == "low" and "fake" not in r.explanation_en.lower()


async def test_news_tagger_fallback_without_llm():
    out = await tag("Coimbatore man loses Rs 12 lakh in digital arrest scam",
                    "Fraudsters posing as CBI officers kept him on a video call and told him not to tell anyone.")
    assert out["scam_type"] == "digital_arrest" and out["region"] == "Coimbatore"
    assert 1 <= len(out["red_flags"]) <= 3


# ---- warnings are not asks ----

AWARENESS = ("Cyber safety tip: do not click unknown links, never share your OTP "
             "and never pay any fee to get a government benefit.")


async def test_awareness_post_with_warnings_is_low(request_factory):
    r = await verify(request_factory(AWARENESS))
    assert r.risk_level == "low"
    assert not {f.code for f in r.red_flags} & {"ask_click", "ask_otp", "ask_pay"}


async def test_real_ask_after_a_warning_still_counts(request_factory):
    r = await verify(request_factory("Do not click unknown links. Click here to claim your free gift: gift-claim.site"))
    assert "ask_click" in {f.code for f in r.red_flags}


def test_negation_in_tamil_and_hindi():
    from kavach.analysis.bait import ask_mentions
    assert ask_mentions("ஓடிபி யாருக்கும் சொல்ல வேண்டாம்")["ask_otp"] == "warned"
    assert ask_mentions("ஓடிபி அனுப்பவும்")["ask_otp"] == "ask"
    assert ask_mentions("OTP kisi ko mat batana")["ask_otp"] == "warned"


def test_conditional_threat_is_still_an_ask():
    from kavach.analysis.bait import ask_mentions
    assert ask_mentions("If you do not register today you lose the benefit")["ask_register"] == "ask"


# ---- LLM replies are strictly typed ----

PLAIN = "The new bus stand in Coimbatore opens next week."


@respx.mock
async def test_string_false_is_not_read_as_true(request_factory, llm_on, llm_reply):
    respx.post(llm_on).mock(return_value=httpx.Response(200, json=llm_reply(
        {"asks": [], "claims_government_scheme": "false"})))
    r = await verify(request_factory(PLAIN))
    assert r.confidence == "normal" and r.risk_level == "low"
    assert "factcheck.pib.gov.in" not in r.explanation_en      # bool("false") would have added this


@respx.mock
async def test_string_true_is_accepted(request_factory, llm_on, llm_reply):
    respx.post(llm_on).mock(return_value=httpx.Response(200, json=llm_reply(
        {"asks": [], "claims_government_scheme": "true"})))
    r = await verify(request_factory(PLAIN))
    assert "factcheck.pib.gov.in" in r.explanation_en


@respx.mock
async def test_non_boolean_scheme_value_is_ignored(request_factory, llm_on, llm_reply):
    respx.post(llm_on).mock(return_value=httpx.Response(200, json=llm_reply(
        {"asks": [], "claims_government_scheme": 1})))
    r = await verify(request_factory(PLAIN))
    assert "factcheck.pib.gov.in" not in r.explanation_en


@respx.mock
async def test_malformed_asks_falls_back_to_keywords(request_factory, llm_on, llm_reply):
    respx.post(llm_on).mock(return_value=httpx.Response(200, json=llm_reply(
        {"asks": "click", "claims_government_scheme": True})))
    r = await verify(request_factory(PLAIN))
    assert r.confidence == "lower" and r.risk_level == "low"


@respx.mock
async def test_llm_cannot_turn_a_warning_into_an_ask(request_factory, llm_on, llm_reply):
    # Contradiction: the post only warns, but the LLM claims it asks to click and share the OTP.
    respx.post(llm_on).mock(return_value=httpx.Response(200, json=llm_reply(
        {"asks": ["click", "otp", "made_up"], "claims_government_scheme": False})))
    r = await verify(request_factory(AWARENESS))
    assert r.risk_level == "low" and r.confidence == "normal"


@respx.mock
async def test_llm_can_add_an_ask_the_keywords_missed(request_factory, llm_on, llm_reply):
    respx.post(llm_on).mock(return_value=httpx.Response(200, json=llm_reply(
        {"asks": ["pay"], "claims_government_scheme": False})))
    r = await verify(request_factory("Kindly transfer 500 rupees to receive the relief amount."))
    assert "ask_pay" in {f.code for f in r.red_flags}
