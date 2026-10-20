# Member 3: news fetcher (section 8-G). Reads the configured RSS feeds, keeps scam-related items,
# asks Member 2's tagger to label them, and stores 20-30 in news_item.
import asyncio, html, json, logging, os, re
from datetime import datetime, timezone
from time import mktime

import feedparser
import httpx
from sqlmodel import select

from kavach.analysis.news_tagger import tag
from kavach.config import settings
from kavach.db import NewsItem, get_session

log = logging.getLogger("kavach.news")

KEEP = re.compile(r"scam|fraud|cyber|phish|digital arrest|ठगी|धोखाधड़ी|साइबर|மோசடி|சைபர்", re.I)
MAX_ITEMS = 30
FETCH_TIMEOUT = 8
DEMO_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "web", "public", "demo", "news.json")


def clean(text: str, limit: int = 240) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def safe_url(url: str | None) -> str | None:
    """Links are rendered as hrefs, so only plain web links are allowed."""
    return url if url and re.match(r"^https?://", url, re.I) else None


def parse_entries(raw: bytes | str) -> list[dict]:
    parsed = feedparser.parse(raw)
    out = []
    for e in parsed.entries:
        url, title = safe_url(e.get("link")), clean(e.get("title", ""), 200)
        summary = clean(e.get("summary", ""))
        if not url or not title or not KEEP.search(f"{title} {summary}"):
            continue
        ts = e.get("published_parsed") or e.get("updated_parsed")
        when = datetime.fromtimestamp(mktime(ts), timezone.utc).isoformat() if ts else None
        out.append({"url": url, "title": title, "summary": summary, "published_at": when})
    return out


async def _get_feed(client: httpx.AsyncClient, url: str) -> list[dict]:
    try:
        r = await client.get(url, follow_redirects=True)
        r.raise_for_status()
        return parse_entries(r.content)
    except Exception as e:      # a blocked or slow feed must never stop startup
        log.warning("news feed skipped (%s): %s", url, type(e).__name__)
        return []


async def refresh() -> int:
    """Returns the number of items now stored. Never raises."""
    try:
        feeds = settings.NEWS_FEEDS
        if not feeds:
            return _count()
        async with httpx.AsyncClient(timeout=FETCH_TIMEOUT, headers={"User-Agent": "KavachHackathon/0.1"}) as c:
            batches = await asyncio.gather(*(_get_feed(c, u) for u in feeds))
        seen, items = set(), []
        for batch in batches:
            for it in batch:
                if it["url"] not in seen:
                    seen.add(it["url"])
                    items.append(it)
        items.sort(key=lambda i: i["published_at"] or "", reverse=True)
        for it in items[:MAX_ITEMS]:
            try:
                t = await tag(it["title"], it["summary"])
            except Exception:
                t = {}
            it["scam_type"], it["region"] = t.get("scam_type") or "unknown", t.get("region")
        _store(items[:MAX_ITEMS])
        return _count()
    except Exception:
        log.exception("news refresh failed")
        return 0


def _count() -> int:
    with get_session() as db:
        return len(db.exec(select(NewsItem)).all())


def _store(items: list[dict]) -> None:
    with get_session() as db:
        have = {r.url for r in db.exec(select(NewsItem)).all()}
        for it in items:
            if it["url"] not in have:
                db.add(NewsItem(url=it["url"], title=it["title"], summary=it["summary"],
                                published_at=it["published_at"], scam_type=it.get("scam_type"),
                                region=it.get("region")))
        db.commit()
        rows = db.exec(select(NewsItem).order_by(NewsItem.id.desc())).all()
        for old in rows[60:]:        # keep the table small
            db.delete(old)
        db.commit()


def load_demo() -> list[dict]:
    """Hand-prepared items from real articles (web/public/demo/news.json). Every item must carry its URL."""
    try:
        with open(DEMO_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    return [d for d in data if isinstance(d, dict) and safe_url(d.get("url")) and d.get("title")]
