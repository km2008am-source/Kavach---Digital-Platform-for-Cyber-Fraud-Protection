"""SQLite connection and schema helpers."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from kavach.config import settings


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    language TEXT NOT NULL DEFAULT 'en',
    guardian_number TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    user_id TEXT PRIMARY KEY
        REFERENCES users(user_id) ON DELETE CASCADE,
    state TEXT NOT NULL DEFAULT 'IDLE',
    data_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    status TEXT NOT NULL DEFAULT 'open',
    evidence_json TEXT NOT NULL DEFAULT '{}',
    acknowledgement_number TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS processed_messages (
    message_id TEXT PRIMARY KEY,
    processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def connect(database_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(database_path or settings.database_path)

    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(path), timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(database_path: str | Path | None = None) -> None:
    with connect(database_path) as connection:
        connection.executescript(SCHEMA)


@contextmanager
def session(
    database_path: str | Path | None = None,
) -> Iterator[sqlite3.Connection]:
    connection = connect(database_path)

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()