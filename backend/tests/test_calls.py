"""Call Shield transcripts: spoken, lower-case, unpunctuated text from speech recognition.

Member 2 plays the fake customs officer in the live demo, so these must be caught with the
LLM and the internet OFF (the conftest fixture turns both off for every test).
"""
import pytest

from kavach.analysis.scam_check import analyze

DEMO_SCAMS = [
    "sir this is customs, your parcel has drugs, press 1",
    "hello i am calling from customs your courier parcel has been stopped there are illegal items inside "
    "you must speak to the officer now",
    "this is the customs officer from chennai airport a parcel with your aadhaar number contains mdma "
    "do not cut the call",
    "madam this is cbi you are involved in a money laundering case stay on this call and do not tell your family",
]
LEGIT_CALLS = [
    "hello this is the courier boy your parcel will come tomorrow morning will you be at home",
    "hi this is your son i reached the office safely",
    "this is the bank calling to say your fixed deposit has matured please visit the branch",
]


@pytest.mark.parametrize("text", DEMO_SCAMS)
async def test_demo_scam_calls_are_caught_offline(request_factory, text):
    r = await analyze(request_factory(text, input_type="transcript"))
    assert r.risk_level in ("medium", "high"), (r.risk_score, text)
    assert r.red_flags


@pytest.mark.parametrize("text", LEGIT_CALLS)
async def test_ordinary_calls_stay_low(request_factory, text):
    r = await analyze(request_factory(text, input_type="transcript"))
    assert r.risk_level == "low", (r.risk_score, text)
