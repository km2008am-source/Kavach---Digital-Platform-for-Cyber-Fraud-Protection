"""SQLite tables for the website: simulator scores and tagged news.

They live in the same database file as Scam Pulse, so Pulse can mark a wave "confirmed" when
the news has reported the same scam type. No simulator transcript is ever stored, only scores.
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from kavach.web_settings import settings

_path: str | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS sim_session (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    language TEXT NOT NULL,
    turns_json TEXT NOT NULL DEFAULT '[]',
    pre_score INTEGER,
    post_score INTEGER,
    final_score INTEGER,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS news_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    published_at TEXT,
    scam_type TEXT,
    region TEXT,
    summary TEXT
);
"""

MAX_NEWS_KEPT = 60


def configure(path: str | None) -> None:
    """Point the store at another SQLite file (tests use a temp file)."""
    global _path
    _path = path


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(_path or settings.DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def init() -> None:
    with _connect():
        pass


# ---- simulator ----
def save_sim(session_id: str, scenario_id: str, language: str, turns: list[dict],
             pre_score: int | None, post_score: int | None, final_score: int | None) -> None:
    with _connect() as conn:
        conn.execute(
            """INSERT INTO sim_session (id, scenario_id, language, turns_json, pre_score, post_score, final_score,
                                        created_at)
               VALUES (?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET turns_json=excluded.turns_json, pre_score=excluded.pre_score,
                   post_score=excluded.post_score, final_score=excluded.final_score""",
            (session_id, scenario_id, language, json.dumps(turns), pre_score, post_score, final_score,
             datetime.now(timezone.utc).isoformat()))


def get_sim(session_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM sim_session WHERE id = ?", (session_id,)).fetchone()
    return dict(row) if row else None


# ---- news ----
def list_news(limit: int = 30) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM news_item ORDER BY published_at DESC, id DESC LIMIT ?",
                            (limit,)).fetchall()
    return [dict(r) for r in rows]


def count_news() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM news_item").fetchone()[0]


def store_news(items: list[dict]) -> None:
    with _connect() as conn:
        for it in items:
            conn.execute(
                """INSERT OR IGNORE INTO news_item (url, title, summary, published_at, scam_type, region)
                   VALUES (?,?,?,?,?,?)""",
                (it["url"], it["title"], it.get("summary"), it.get("published_at"), it.get("scam_type"),
                 it.get("region")))
        conn.execute("DELETE FROM news_item WHERE id NOT IN (SELECT id FROM news_item ORDER BY id DESC LIMIT ?)",
                     (MAX_NEWS_KEPT,))
