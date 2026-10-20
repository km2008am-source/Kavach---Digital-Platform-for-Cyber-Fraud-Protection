"""Language helpers with Tamil and English support."""

from deep_translator import GoogleTranslator
from langdetect import DetectorFactory, LangDetectException, detect

DetectorFactory.seed = 0

SUPPORTED_LANGUAGES = {"en", "ta"}


def detect_language(text: str, default: str = "en") -> str:
    """Return 'en' or 'ta'; use default when detection is uncertain."""
    cleaned = text.strip()
    if not cleaned:
        return default

    # Tamil Unicode block: Tamil characters are U+0B80 through U+0BFF.
    if any("\u0b80" <= char <= "\u0bff" for char in cleaned):
        return "ta"

    try:
        detected = detect(cleaned)
    except LangDetectException:
        return default

    return detected if detected in SUPPORTED_LANGUAGES else default


async def translate(text: str, source: str, target: str) -> str:
    """Translate text, preserving it when translation isn't needed."""
    if not text or source == target:
        return text

    if source not in SUPPORTED_LANGUAGES or target not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language pair: {source} -> {target}")

    # deep-translator's GoogleTranslator call is synchronous.
    return GoogleTranslator(source=source, target=target).translate(text)


async def stt(audio_path: str, language: str = "en") -> str:
    """Speech-to-text placeholder; connect a provider before voice-note use."""
    raise NotImplementedError(
        "Speech-to-text provider is not configured yet "
        f"(audio={audio_path!r}, language={language!r})"
    )


async def tts(text: str, language: str = "en") -> str:
    """Text-to-speech placeholder; connect a provider before voice replies."""
    raise NotImplementedError(
        "Text-to-speech provider is not configured yet "
        f"(language={language!r})"
    )