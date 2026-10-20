# M1 owns db.py. This file carries only Member 3's two tables (sim_session, news_item from section 5),
# so M1 can merge them into the real db.py; table and field names follow the frozen schema.
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Session, create_engine
from kavach.config import settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SimSession(SQLModel, table=True):
    __tablename__ = "sim_session"
    id: str = Field(primary_key=True)
    scenario_id: str
    language: str
    turns_json: str = "[]"
    pre_score: Optional[int] = None
    post_score: Optional[int] = None   # M3 owns this table: after-quiz score, added for the before/after card
    final_score: Optional[int] = None
    created_at: str = Field(default_factory=_now)


class NewsItem(SQLModel, table=True):
    __tablename__ = "news_item"
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    title: str
    published_at: Optional[str] = None
    scam_type: Optional[str] = None
    region: Optional[str] = None
    summary: Optional[str] = None


engine = create_engine(settings.DB_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
