# Member 3: simulator scoring. Deterministic on purpose: the fallback judge, the final score and
# the debrief never depend on the LLM, so they work when the LLM is down and read the same every time.
import re

# Tamil keyword lists: substring match (\b is unreliable in Tamil script). Confirm with a native speaker.
_EN_STRONG_RESIST = re.compile(
    r"\b(?:hang(?:ing)? up|hung up|disconnect(?:ing)?|1930|cyber ?crime|scam(?:mer)?|fraud|fake|"
    r"i (?:will|am going to|'ll|shall) (?:call|verify|check|tell|report)|"
    r"call(?:ing)? (?:the )?police|going to the police|report(?:ing)? (?:you|this)|"
    r"call you back|call back|my (?:son|daughter|husband|wife|family|lawyer))\b", re.I)
_EN_STRONG_COMPLY = re.compile(
    r"\b(?:i (?:will|'ll|am going to|shall) (?:pay|send|transfer|give|share)|"
    r"sending (?:it )?(?:now|the)|transferring|paying now|here is my|my (?:otp|pin|aadhaar|card) is)\b", re.I)
_EN_REFUSE = re.compile(
    r"\b(?:no(?! (?:idea|clue|problem|way to))|refuse|never|won'?t|will not|not (?:going to )?(?:pay|send|give|share|tell)|"
    r"(?:don'?t|do not) (?:want|believe|trust))\b", re.I)
_EN_COMPLY = re.compile(
    r"\b(?:ok(?:ay)?|yes(?: sir)?|sir|please|what should i do|how much|tell me how|"
    r"i am (?:scared|afraid)|don'?t arrest|help me|i am innocent)\b", re.I)
_EN_HANGUP = re.compile(r"\b(?:hang(?:ing)? up|hung up|disconnect(?:ing)?|1930|call(?:ing)? (?:the )?police)\b", re.I)

_TA_STRONG_RESIST = ["1930", "மோசடி", "ஏமாற்று", "போலீஸ்", "துண்டிக்", "வைத்து விடுகிறேன்", "வைக்கிறேன்",
                     "சரிபார்", "குடும்பத்தினரிடம்", "திரும்ப அழைக்கிறேன்"]
_TA_STRONG_COMPLY = ["அனுப்புகிறேன்", "செலுத்துகிறேன்", "அனுப்பி விடுகிறேன்", "கட்டுகிறேன்"]
_TA_REFUSE = ["மாட்டேன்", "இல்லை", "முடியாது", "வேண்டாம்"]
_TA_COMPLY = ["சரி", "ஐயா", "பயமாக", "என்ன செய்ய", "தயவு"]
_TA_HANGUP = ["1930", "துண்டிக்", "வைத்து விடுகிறேன்", "வைக்கிறேன்"]


# "don't hang up", "I'm not going to call the police", "this is not a scam": a negated phrase means the opposite.
_NEG = re.compile(r"(?:don'?t|do not|not|never|won'?t|will not|cannot|can'?t|no)\W+(?:\w+\W+){0,3}$", re.I)


def _affirmed(pattern: re.Pattern, text: str) -> bool:
    """True if the pattern matches somewhere that is not negated just before it."""
    return any(not _NEG.search(text[:m.start()]) for m in pattern.finditer(text))


def _any(words: list[str], text: str) -> bool:
    return any(w in text for w in words)


def heuristic_score(text: str) -> int:
    """0-10: did the user resist this turn? Order matters: a firm refusal beats polite filler."""
    t = text or ""
    if _affirmed(_EN_STRONG_RESIST, t) or _any(_TA_STRONG_RESIST, t):
        return 9
    if _EN_STRONG_COMPLY.search(t) or _any(_TA_STRONG_COMPLY, t):
        return 0
    if _EN_REFUSE.search(t) or _any(_TA_REFUSE, t):
        return 7
    if _EN_COMPLY.search(t) or _any(_TA_COMPLY, t):
        return 2
    return 5


def is_complying(text: str) -> bool:
    t = text or ""
    if _affirmed(_EN_STRONG_RESIST, t) or _any(_TA_STRONG_RESIST, t):
        return False
    return bool(_EN_STRONG_COMPLY.search(t) or _any(_TA_STRONG_COMPLY, t))


def is_hangup(text: str) -> bool:
    t = text or ""
    if t.strip().endswith("?"):      # "should I call 1930?" is a question, not a hang-up
        return False
    return bool(_affirmed(_EN_HANGUP, t) or _any(_TA_HANGUP, t))


def final_score(scores: list[int]) -> int:
    """Average turn score x 10, so 0-100."""
    return round(sum(scores) / len(scores) * 10) if scores else 0


def quiz_score(answers: list[str], quiz: list[dict]) -> int:
    """Percent correct; a missing answer counts as wrong."""
    if not quiz:
        return 0
    right = sum(1 for i, q in enumerate(quiz)
                if i < len(answers) and str(answers[i]).strip().lower() == q["a"])
    return round(100 * right / len(quiz))


LABEL = {
    "en": {"urgency": "Urgency", "authority": "Authority", "isolation": "Isolation",
           "fear": "Fear", "secrecy": "Secrecy", "payment_push": "Payment push"},
    "ta": {"urgency": "அவசரம்", "authority": "அதிகாரம்", "isolation": "தனிமைப்படுத்தல்",
           "fear": "பயம்", "secrecy": "ரகசியம்", "payment_push": "பணம் கேட்பு"},
}
ADVICE = {
    "en": {
        "urgency": "They rushed you. Real cases are never closed in 30 minutes. Say: \"I will check and call back.\"",
        "authority": "They used an official-sounding title. Say: \"I will call the official number myself.\"",
        "isolation": "They told you to tell nobody. Real officers never say that. Tell your family right away.",
        "secrecy": "They told you to tell nobody. Real officers never say that. Tell your family right away.",
        "fear": "They threatened arrest. Nobody can be arrested over a video call.",
        "payment_push": "They asked for money. A real officer never asks for a deposit to clear your name.",
    },
    "ta": {
        "urgency": "உங்களை அவசரப்படுத்தினார்கள். \"சரிபார்த்துவிட்டுத் திரும்ப அழைக்கிறேன்\" என்று சொல்லுங்கள்.",
        "authority": "அதிகாரி போல் பேசினார்கள். \"அதிகாரப்பூர்வ எண்ணை நானே அழைக்கிறேன்\" என்று சொல்லுங்கள்.",
        "isolation": "யாரிடமும் சொல்லக்கூடாது என்றார்கள். உண்மையான அதிகாரிகள் இப்படிச் சொல்ல மாட்டார்கள். உடனே குடும்பத்தினரிடம் சொல்லுங்கள்.",
        "secrecy": "யாரிடமும் சொல்லக்கூடாது என்றார்கள். உண்மையான அதிகாரிகள் இப்படிச் சொல்ல மாட்டார்கள். உடனே குடும்பத்தினரிடம் சொல்லுங்கள்.",
        "fear": "கைது செய்வதாகப் பயமுறுத்தினார்கள். வீடியோ அழைப்பில் யாரையும் கைது செய்ய முடியாது.",
        "payment_push": "பணம் கேட்டார்கள். பெயரை விடுவிக்க உண்மையான அதிகாரி பணம் கேட்க மாட்டார்.",
    },
}
_T = {
    "en": {"score": "Your resilience score: {n} out of 100.", "held": "held firm", "slipped": "you slipped",
           "close": "Best move every time: hang up and call 1930 yourself.",
           "stopped": "You typed something that looks like real ID data. Never share Aadhaar or card numbers "
                      "with a caller, even one who sounds official."},
    "ta": {"score": "உங்கள் தாங்கும் திறன் மதிப்பெண்: 100-க்கு {n}.", "held": "உறுதியாக இருந்தீர்கள்",
           "slipped": "தவறவிட்டீர்கள்",
           "close": "ஒவ்வொரு முறையும் சிறந்த வழி: அழைப்பைத் துண்டித்து நீங்களே 1930-ஐ அழையுங்கள்.",
           "stopped": "உண்மையான அடையாளத் தகவல் போல ஏதோ தட்டச்சு செய்துள்ளீர்கள். அழைப்பவர் அதிகாரி போல் "
                      "பேசினாலும் ஆதார் அல்லது கார்டு எண்களைப் பகிராதீர்கள்."},
}


def build_debrief(turns: list[dict], score: int, language: str = "en", stopped_for_data: bool = False) -> str:
    """turns: [{"tactics": [...faced...], "score": int}]. A tactic counts as resisted when the
    user's average score on the turns that faced it is 6 or more."""
    lang = language if language in _T else "en"
    t = _T[lang]
    lines = [t["score"].format(n=score)]
    if stopped_for_data:
        lines.append(t["stopped"])
    by_tactic: dict[str, list[int]] = {}
    for turn in turns:
        for tac in turn.get("tactics", []):
            by_tactic.setdefault(tac, []).append(turn["score"])
    for tac, scores in by_tactic.items():       # insertion order = order first met
        held = sum(scores) / len(scores) >= 6
        name = LABEL[lang].get(tac, tac)
        if held:
            lines.append(f"{name}: {t['held']}.")
        else:
            lines.append(f"{name}: {t['slipped']}. {ADVICE[lang].get(tac, '')}".strip())
    lines.append(t["close"])
    return "\n".join(lines)
