"""Application settings loaded from environment variables."""

from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_FILE, override=False)
@dataclass(frozen=True)
class Settings:
    app_env: str
    database_path: Path
    files_dir: Path
    dry_run: bool
    wa_verify_token: str
    wa_token: str
    wa_phone_id: str
    graph_version: str
    whatsapp_provider: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_whatsapp_from: str
    twilio_webhook_url: str
    telegram_bot_token: str
    telegram_webhook_secret: str


def load_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_path=Path(os.getenv("DATABASE_PATH", "kavach.db")),
        files_dir=Path(os.getenv("FILES_DIR", "files")),
        dry_run=os.getenv("DRY_RUN", "1").strip().lower()
        in {"1", "true", "yes"},
        wa_verify_token=os.getenv("WA_VERIFY_TOKEN", ""),
        wa_token=os.getenv("WA_TOKEN", ""),
        wa_phone_id=os.getenv("WA_PHONE_ID", ""),
        graph_version=os.getenv("GRAPH_VERSION", "v23.0"),
        whatsapp_provider=os.getenv("WHATSAPP_PROVIDER", "meta").strip().lower(),
        twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
        twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
        twilio_whatsapp_from=os.getenv("TWILIO_WHATSAPP_FROM", ""),
        twilio_webhook_url=os.getenv("TWILIO_WEBHOOK_URL", ""),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_webhook_secret=os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip(),
    )


settings = load_settings()