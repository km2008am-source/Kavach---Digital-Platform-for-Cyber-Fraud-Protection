"""English and Hindi language helpers, speech-to-text, and text-to-speech."""

import asyncio
import os
import uuid
from functools import lru_cache
from pathlib import Path

from deep_translator import GoogleTranslator
from langdetect import DetectorFactory, LangDetectException, detect

DetectorFactory.seed = 0

SUPPORTED_LANGUAGES = {"en", "hi"}


def detect_language(text: str, default: str = "en") -> str:
    """Detect English or Hindi; use default when detection is uncertain."""
    cleaned = text.strip()
    if not cleaned:
        return default

    # Hindi uses the Devanagari Unicode block.
    if any("\u0900" <= char <= "\u097f" for char in cleaned):
        return "hi"

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

    return await asyncio.to_thread(
        GoogleTranslator(source=source, target=target).translate,
        text,
    )


@lru_cache(maxsize=1)
def _whisper_model():
    from faster_whisper import WhisperModel

    return WhisperModel("base", device="cpu", compute_type="int8")


def _transcribe(audio_path: str, language: str) -> str:
    # faster-whisper detects the spoken language when language=None.
    whisper_language = None if language == "auto" else language
    segments, _ = _whisper_model().transcribe(
        audio_path,
        language=whisper_language,
        beam_size=5,
        vad_filter=True,
    )

    return " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    ).strip()


async def stt(audio_path: str, language: str = "en") -> str:
    """Transcribe an English or Hindi voice note."""
    if language != "auto" and language not in SUPPORTED_LANGUAGES:
        language = "en"

    return await asyncio.to_thread(_transcribe, audio_path, language)


def _tts_sync(text: str, language: str) -> str:
    from gtts import gTTS

    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported speech language: {language}")
    if not text.strip():
        raise ValueError("Text for speech cannot be empty")

    output_dir = Path(os.getenv("FILES_DIR", "files"))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"reply-{uuid.uuid4().hex}.mp3"

    gTTS(text=text[:1500], lang=language).save(str(output_path))
    return str(output_path)


async def tts(text: str, language: str = "en") -> str:
    """Create an MP3 speech reply in English or Hindi."""
    return await asyncio.to_thread(_tts_sync, text, language)