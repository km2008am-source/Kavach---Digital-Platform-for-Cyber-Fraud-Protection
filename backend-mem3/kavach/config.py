# M1 owns config.py. Minimal version so Member 3's modules run; M1's real file replaces it.
# Every name below comes from the frozen .env.example, except the ones marked NEW.
import os
from dotenv import load_dotenv

load_dotenv()


def _flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip() in ("1", "true", "True")


class Settings:
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    DB_URL = os.getenv("DB_URL", "sqlite:///kavach.db")
    HASH_SALT = os.getenv("HASH_SALT", "change-me")
    WA_TOKEN = os.getenv("WA_TOKEN", "")
    WA_PHONE_ID = os.getenv("WA_PHONE_ID", "")
    WA_VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN", "")
    GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v21.0")
    DRY_RUN = _flag("DRY_RUN")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_NUMBER = os.getenv("TWILIO_NUMBER", "")
    DEMO_USER_NUMBER = os.getenv("DEMO_USER_NUMBER", "")
    DEMO_MODE = _flag("DEMO_MODE")
    # NEW (needs M1 sign-off, section 5 says env names are frozen): language of the demo user's alerts
    DEMO_USER_LANG = os.getenv("DEMO_USER_LANG", "en")
    # NEW: Twilio Gather speech language; "en-IN" is safe, try "ta-IN" after checking Twilio's list
    CALL_SPEECH_LANG = os.getenv("CALL_SPEECH_LANG", "en-IN")
    # NEW: comma-separated RSS URLs for the news feed; empty = use web/public/demo/news.json.
    # Add only feeds you have opened from the venue network; the guide leaves the choice to the team.
    NEWS_FEEDS = [u.strip() for u in os.getenv("NEWS_FEEDS", "").split(",") if u.strip()]
    # NEW: origins allowed by CORS for the Vite dev server
    WEB_ORIGINS = [o for o in os.getenv("WEB_ORIGINS", "http://localhost:5173").split(",") if o]


settings = Settings()
