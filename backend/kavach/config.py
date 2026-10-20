"""Application settings loaded from environment variables."""

from dataclasses import dataclass
import os
from pathlib import Path


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
    )


settings = load_settings()