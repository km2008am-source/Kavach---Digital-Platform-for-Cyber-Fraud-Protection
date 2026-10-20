"""Person 2 (analysis) settings, read from the environment / `backend/.env`.

Lives next to Person 1's `kavach/config.py` instead of replacing it: the analysis engine
needs LLM, threat-intel and hashing settings that the WhatsApp layer does not. Shared
names (`APP_ENV`, `DATABASE_PATH`) are read from the same environment variables, so both
halves agree on the environment and use the same SQLite file.
"""
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]       # .../backend
PROJECT_DIR = BACKEND_DIR.parent                         # repository root (data/, eval/)

DEFAULT_SALT = "change-me"
WEAK_SALTS = {"", DEFAULT_SALT, "changeme", "salt", "secret", "kavach"}
MIN_SALT_LENGTH = 16
# Person 1's config defaults APP_ENV to "development"; accept both naming styles.
ENV_ALIASES = {"development": "dev", "local": "dev", "testing": "test", "production": "prod", "staging": "demo"}


def salt_is_weak(salt: str) -> bool:
    return salt.strip().lower() in WEAK_SALTS or len(salt.strip()) < MIN_SALT_LENGTH


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    # dev/test: local work, weak salt tolerated (with a warning). demo/prod (or any unknown
    # value): anything a real person's phone talks to; a weak HASH_SALT stops the app.
    APP_ENV: str = "dev"
    DATABASE_PATH: str = "kavach.db"                     # same variable as Person 1's config
    HASH_SALT: str = DEFAULT_SALT
    LLM_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""
    SAFE_BROWSING_KEY: str = ""
    VT_API_KEY: str = ""
    DEMO_MODE: bool = False
    NETWORK_CHECKS: bool = True       # 0 = skip WHOIS/Safe Browsing/VirusTotal (offline tests)
    PULSE_EMBEDDINGS: str = "tfidf"   # "e5" = sentence-transformers, "tfidf" = no download
    MAX_FILE_BYTES: int = 20 * 1024 * 1024   # guide section 11: max 20 MB per uploaded file
    TESSERACT_CMD: str = ""           # path to tesseract(.exe); empty = PATH or the Windows default
    BLOCKLIST_PATH: str = ""          # local URLhaus list (scripts/update_blocklist.py); empty = default

    @field_validator("APP_ENV", mode="before")
    @classmethod
    def _normalise_env(cls, v):
        v = str(v or "dev").strip().lower()
        return ENV_ALIASES.get(v, v)

    @model_validator(mode="after")
    def _salt_guard(self):
        # Reporter IDs in Scam Pulse are HMAC'd with HASH_SALT. With a known or short salt, anyone
        # holding the database can hash every Indian mobile number and re-identify reporters.
        if self.APP_ENV not in ("dev", "test") and salt_is_weak(self.HASH_SALT):
            raise ValueError(
                f"HASH_SALT must be a random secret of at least {MIN_SALT_LENGTH} characters when "
                f"APP_ENV={self.APP_ENV}. Generate one with: "
                "python -c \"import secrets; print(secrets.token_hex(32))\"")
        return self


settings = Settings()
