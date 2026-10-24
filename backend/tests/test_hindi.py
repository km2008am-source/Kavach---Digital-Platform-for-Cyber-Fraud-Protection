"""Hindi and Hinglish: scams are caught by the rules alone (LLM off) and genuine Hindi messages,
including bank warnings that mention the OTP, are not flagged."""
import pytest

from kavach.analysis import bait, rules, scam_check

SCAMS = [
    "आपका एसबीआई खाता आज ही ब्लॉक हो जाएगा। केवाईसी अपडेट करने के लिए तुरंत अपना ओटीपी बताएं।",
    "मैं सीबीआई अधिकारी बोल रहा हूँ। आपके नाम पर मनी लॉन्ड्रिंग का केस दर्ज है। आप डिजिटल अरेस्ट में हैं, "
    "कॉल मत काटिए और किसी को मत बताइए।",
    "आपके नाम का पार्सल कस्टम्स ने जब्त कर लिया है, उसमें ड्रग्स मिले हैं। अधिकारी से बात करने के लिए 1 दबाएं।",
    "बधाई हो! आपने 25 लाख की लॉटरी जीत ली है। इनाम पाने के लिए 5000 रुपये शुल्क जमा करें।",
    "घर बैठे रोज़ कमाएं 3000 रुपये! पार्ट टाइम नौकरी, बस वीडियो लाइक करें। रजिस्ट्रेशन फीस भरें।",
    "Sir aapka account band ho jayega aaj hi. KYC ke liye OTP bata do jaldi.",
    "Aapko 2000 cashback mila hai, paise lene ke liye QR code scan karke UPI PIN daalein.",
    "पीएम मुफ्त लैपटॉप योजना 2026: अभी रजिस्टर करें और आधार नंबर भेजें। इस मैसेज को 10 ग्रुप में शेयर करें।",
    "आपके फोटो वायरल कर देंगे सभी कॉन्टैक्ट्स को, अभी 10000 पैसे भेजो वरना",
]

GENUINE = [
    "123456 आपका ओटीपी है। इसे किसी के साथ साझा न करें। - एसबीआई",
    "प्रिय ग्राहक, आपके खाते में ₹5,000 जमा किए गए हैं। उपलब्ध शेष ₹12,340।",
    "माँ, मैं अभी मीटिंग में हूँ, शाम को फोन करूँगा।",
    "आपका ऑर्डर कल तक डिलीवर हो जाएगा। ट्रैक करने के लिए ऐप खोलें।",
    "Bhai kal cricket khelne chalein? Shaam 5 baje ground pe milte hain.",
    "आपकी बिजली का बिल ₹1,240 है, अंतिम तिथि 28 अक्टूबर। भुगतान आधिकारिक ऐप से करें।",
    "डॉक्टर अपॉइंटमेंट कल सुबह 10 बजे है, कृपया समय पर पहुँचें।",
    "बैंक कभी भी फोन पर ओटीपी या पिन नहीं मांगता। किसी को अपना ओटीपी न बताएं।",
]


@pytest.mark.parametrize("text", SCAMS)
async def test_hindi_scam_is_flagged_without_llm(text, request_factory):
    r = await scam_check.analyze(request_factory(text, language="hi"))
    assert r.risk_level in ("medium", "high"), (r.risk_score, text)


@pytest.mark.parametrize("text", GENUINE)
async def test_genuine_hindi_message_is_not_flagged(text, request_factory):
    r = await scam_check.analyze(request_factory(text, language="hi"))
    assert r.risk_level == "low" and r.red_flags == [], (r.risk_score, text)


async def test_hindi_scam_types(request_factory):
    expected = {0: "kyc_update", 1: "digital_arrest", 2: "courier_customs", 3: "lottery_prize", 4: "job_offer",
                7: "fake_scheme"}
    for i, scam_type in expected.items():
        r = await scam_check.analyze(request_factory(SCAMS[i], language="hi"))
        assert r.scam_type.value == scam_type, SCAMS[i]


def test_nukta_spelling_matches_both_ways():
    for text in ("आपको गिरफ़्तार किया जाएगा", "आपको गिरफ्तार किया जाएगा"):
        assert "threat_arrest" in rules.rule_flags(text)[1]


def test_hindi_rupee_amount_extracted():
    assert rules.extract_entities("5000 रुपये जमा करें")["amounts"] == ["5000 रुपये"]


def test_hindi_warning_is_advice_not_an_ask():
    assert bait.follow_the_ask("सरकारी योजना के नाम पर किसी को अपना ओटीपी न बताएं।") == []
    assert "ask_otp" in bait.follow_the_ask("योजना का लाभ पाने के लिए अपना ओटीपी भेजें।")
