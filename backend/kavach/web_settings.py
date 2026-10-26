"""Settings for the website API and Call Shield.

Read from the same backend/.env as the rest of the app. Values that already exist elsewhere
(Twilio token, demo mode, the database file) are taken from there, so nothing is configured twice.
"""
import os

from kavach.analysis.settings import BACKEND_DIR, settings as analysis_settings
from kavach.config import settings as core_settings


def _list(name: str, default: str = "") -> list[str]:
    return [v.strip() for v in os.getenv(name, default).split(",") if v.strip()]


def _db_path() -> str:
    path = analysis_settings.DATABASE_PATH
    return str(path if os.path.isabs(path) else BACKEND_DIR / path)


class WebSettings:
    # Public HTTPS address Twilio calls back to; used to verify Twilio's request signatures.
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    TWILIO_AUTH_TOKEN = core_settings.twilio_auth_token
    # Who receives Call Shield alerts: a Telegram chat id with WHATSAPP_PROVIDER=telegram.
    DEMO_USER_NUMBER = os.getenv("DEMO_USER_NUMBER", "").strip()
    DEMO_USER_LANG = os.getenv("DEMO_USER_LANG", "en").strip() or "en"
    # Twilio speech-recognition language for the caller's reason.
    CALL_SPEECH_LANG = os.getenv("CALL_SPEECH_LANG", "en-IN").strip() or "en-IN"
    # Comma-separated RSS feeds; empty means the hand-picked demo news is served, labelled as demo.
    NEWS_FEEDS = _list("NEWS_FEEDS")
    # Browser origins allowed to call the API directly (the Vite dev server proxies, so this is rarely needed).
    WEB_ORIGINS = _list("WEB_ORIGINS", "http://localhost:5173,http://localhost:5174")
    DEMO_MODE = analysis_settings.DEMO_MODE
    DB_PATH = _db_path()


settings = WebSettings()
