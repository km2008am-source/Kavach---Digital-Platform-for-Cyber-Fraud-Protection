# Member 3: GET /api/news. Tagged items from the DB, or the hand-prepared demo set (clearly marked).
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import select

from kavach.api.news_fetch import load_demo, safe_url
from kavach.db import NewsItem, get_session

router = APIRouter()


class NewsOut(BaseModel):
    url: str
    title: str
    published_at: Optional[str] = None
    scam_type: Optional[str] = None
    region: Optional[str] = None
    summary: Optional[str] = None
    demo: bool = False        # True = hand-prepared item, not fetched live


@router.get("/api/news", response_model=list[NewsOut])
async def news():
    with get_session() as db:
        rows = db.exec(select(NewsItem).order_by(NewsItem.published_at.desc(), NewsItem.id.desc()).limit(30)).all()
    items = [NewsOut(url=r.url, title=r.title, published_at=r.published_at, scam_type=r.scam_type,
                     region=r.region, summary=r.summary) for r in rows if safe_url(r.url)]
    if items:
        return items
    return [NewsOut(url=d["url"], title=d["title"], published_at=d.get("published_at"),
                    scam_type=d.get("scam_type"), region=d.get("region"), summary=d.get("summary"), demo=True)
            for d in load_demo()[:30]]
