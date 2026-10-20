"""Scam Pulse: detect scam waves from anonymised reports.

Privacy: only medium/high verdicts are stored; text is normalised (links, phones, UPI IDs,
amounts and long numbers replaced by placeholders) BEFORE it is written; the reporter is a
hash; the district is user-chosen, never GPS.

Embeddings: TF-IDF on character n-grams by default (no model download, handles Tamil and
English). Set PULSE_EMBEDDINGS=e5 to use sentence-transformers multilingual-e5-small,
which also groups a Tamil and an English copy of the same template.
"""
import hashlib
import hmac
import json
import re
import sqlite3
import uuid
import warnings
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from kavach.analysis.settings import BACKEND_DIR, PROJECT_DIR, salt_is_weak, settings
from kavach.analysis.models import AnalysisResult, PulseAlert, ScamType

MIN_REPORTS, MIN_REPORTERS = 5, 3
# Cosine distance, average linkage. TF-IDF 0.78 sits between the widest distance inside one
# seed campaign (0.75, reworded copies of a template) and the closest pair of different
# campaigns (0.86, courier vs KYC). e5 0.15 is the guide's untuned starting value.
DISTANCE_THRESHOLD = {"tfidf": 0.78, "e5": 0.15}
SEED_PATH = PROJECT_DIR / "data" / "samples" / "pulse_seed.jsonl"
LANG_NAMES = {"ta": "Tamil", "en": "English", "hi": "Hindi"}

_db_path: str | None = None
_e5 = None
_weak_salt_warned = False


def configure(db_path: str | None) -> None:
    """Point Pulse at another SQLite file (tests use a temp file)."""
    global _db_path
    _db_path = db_path


def _connect() -> sqlite3.Connection:
    path = Path(_db_path or settings.DATABASE_PATH)
    if not path.is_absolute():
        path = BACKEND_DIR / path                   # same file whatever folder the app is started from
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE IF NOT EXISTS report (
        id TEXT PRIMARY KEY, created_at TEXT NOT NULL, channel TEXT, scam_type TEXT NOT NULL,
        risk_level TEXT NOT NULL, district TEXT NOT NULL, language TEXT, normalized_text TEXT NOT NULL,
        reporter_hash TEXT NOT NULL, embedding BLOB)""")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_report_created ON report(created_at)")
    return conn


# ---------- normalise / embed / cluster ----------

def normalize(text: str) -> str:
    text = re.sub(r"https?://\S+|www\.\S+|\b[\w-]+\.(?:xyz|top|in|com|co|info|link|online|site)\b\S*",
                  "<URL>", text, flags=re.I)
    text = re.sub(r"\b[\w.\-]{2,}@[a-zA-Z]{2,}\b", "<UPI>", text)
    text = re.sub(r"(?:\+91[\s-]?)?(?<!\d)[6-9]\d{9}(?!\d)", "<PHONE>", text)
    text = re.sub(r"(?:₹|\brs\.?|\binr)\s?\d[\d,]*(?:\.\d+)?", "<AMOUNT>", text, flags=re.I)
    text = re.sub(r"\d{4,}", "<NUM>", text)
    return re.sub(r"\s+", " ", text).strip()


def _language(text: str) -> str:
    return "ta" if re.search(r"[஀-௿]", text) else "hi" if re.search(r"[ऀ-ॿ]", text) else "en"


def embed(texts: list[str]) -> np.ndarray:
    if settings.PULSE_EMBEDDINGS == "e5":
        global _e5
        if _e5 is None:
            from sentence_transformers import SentenceTransformer
            _e5 = SentenceTransformer("intfloat/multilingual-e5-small")
        return np.asarray(_e5.encode(["query: " + t for t in texts], normalize_embeddings=True))
    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
    return vec.fit_transform(texts).toarray()


def cluster(vectors: np.ndarray) -> np.ndarray:
    if len(vectors) < 2:
        return np.zeros(len(vectors), dtype=int)
    threshold = DISTANCE_THRESHOLD.get(settings.PULSE_EMBEDDINGS, 0.6)
    return AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average",
                                   distance_threshold=threshold).fit_predict(vectors)


def reporter_key(reporter_id: str) -> str:
    """Keyed, salted hash of a reporter ID (HMAC-SHA256 with HASH_SALT).

    Applied on every write, so even if a caller passes a raw phone number the table
    never holds it, and the stored value cannot be reversed by hashing guessed numbers
    without the server-side salt.
    """
    if not reporter_id:
        raise ValueError("reporter_id is required")
    global _weak_salt_warned
    if salt_is_weak(settings.HASH_SALT) and not _weak_salt_warned:
        # config.Settings already refuses a weak salt when APP_ENV is demo or prod.
        warnings.warn("HASH_SALT is the default or too short: Scam Pulse reporter IDs are not protected. "
                      "Set a random HASH_SALT before real users connect.", RuntimeWarning, stacklevel=2)
        _weak_salt_warned = True
    return hmac.new(settings.HASH_SALT.encode(), reporter_id.encode(), hashlib.sha256).hexdigest()


# ---------- public API ----------

def ingest(result: AnalysisResult, text: str, district: str | None, reporter_hash: str,
           channel: str = "whatsapp", created_at: datetime | None = None) -> None:
    """Store one anonymised report. Low-risk (legit) messages are never stored.

    `reporter_hash` is whatever stable per-user ID the caller has (Member 1 passes the
    user's wa_hash); it is hashed again with the salt before storage.
    """
    if result.risk_level not in ("medium", "high") or not district or not text or not reporter_hash:
        return
    norm = normalize(text)
    with _connect() as conn:
        conn.execute("INSERT INTO report VALUES (?,?,?,?,?,?,?,?,?,?)", (
            str(uuid.uuid4()), (created_at or datetime.now(timezone.utc)).isoformat(), channel,
            result.scam_type.value, result.risk_level, district.strip().title(), _language(norm), norm,
            reporter_key(reporter_hash), None))


def _load(hours: int) -> list[sqlite3.Row]:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        return conn.execute("SELECT * FROM report WHERE created_at >= ? ORDER BY created_at", (since,)).fetchall()


def _news_types(hours: int) -> set[str]:
    """Scam types of tagged news items (Member 3's news_item table) in the same window, if present."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    try:
        with _connect() as conn:
            return {r[0] for r in conn.execute(
                "SELECT scam_type FROM news_item WHERE published_at >= ?", (since,)) if r[0]}
    except sqlite3.Error:
        return set()


def _label(scam_type: str, languages: Counter) -> str:
    kind = scam_type.replace("_", "-")
    langs = ", ".join(LANG_NAMES.get(l, l) for l, _ in languages.most_common(2))
    return f"{kind} scam, {langs}"


def alerts(hours: int = 72) -> list[PulseAlert]:
    rows = _load(hours)
    news = _news_types(hours)
    out: list[PulseAlert] = []
    by_district: dict[str, list[sqlite3.Row]] = {}
    for r in rows:
        by_district.setdefault(r["district"], []).append(r)
    for district, items in sorted(by_district.items()):
        if len(items) < MIN_REPORTS:
            continue
        labels = cluster(embed([r["normalized_text"] for r in items]))
        # One alert per text cluster. Clusters are never merged just because they share a scam
        # type and district: two unrelated campaigns must stay two alerts. (With PULSE_EMBEDDINGS=e5
        # a Tamil and an English copy of one template already fall into the same cluster.)
        for lab in sorted(set(labels.tolist())):
            members = [r for r, l in zip(items, labels, strict=True) if l == lab]
            reporters = {r["reporter_hash"] for r in members}
            if len(members) < MIN_REPORTS or len(reporters) < MIN_REPORTERS:
                continue
            scam_type = Counter(r["scam_type"] for r in members).most_common(1)[0][0]
            sample = Counter(r["normalized_text"] for r in members).most_common(1)[0][0]
            # Stable while the cluster grows: keyed on its earliest report, not on type + district.
            cid = hashlib.sha256(f"{district}|{scam_type}|{members[0]['id']}".encode()).hexdigest()[:12]
            out.append(PulseAlert(
                cluster_id=cid, label=_label(scam_type, Counter(r["language"] for r in members)),
                scam_type=ScamType(scam_type), district=district, report_count=len(members),
                distinct_reporters=len(reporters), window_hours=hours,
                confidence="confirmed" if scam_type in news else "emerging", sample_text=sample[:300]))
    return sorted(out, key=lambda a: -a.report_count)


def replay(seed_path: Path = SEED_PATH, spread_minutes: int = 120) -> int:
    """Insert the seed reports with timestamps spread over the last 2 hours (demo spike)."""
    lines = [json.loads(l) for l in seed_path.read_text("utf-8").splitlines() if l.strip()]
    now = datetime.now(timezone.utc)
    with _connect() as conn:
        conn.execute("DELETE FROM report WHERE channel = 'seed'")    # idempotent: pressing Replay twice
        for i, s in enumerate(lines):
            at = now - timedelta(minutes=spread_minutes * (len(lines) - i) / len(lines))
            reporter = reporter_key(s["reporter"])
            conn.execute("INSERT INTO report VALUES (?,?,?,?,?,?,?,?,?,?)", (
                str(uuid.uuid4()), at.isoformat(), "seed", s["scam_type"], s["risk_level"], s["district"],
                s["language"], normalize(s["text"]), reporter, None))
    return len(lines)


def purge(older_than_hours: int = 24 * 30) -> int:
    since = (datetime.now(timezone.utc) - timedelta(hours=older_than_hours)).isoformat()
    with _connect() as conn:
        return conn.execute("DELETE FROM report WHERE created_at < ?", (since,)).rowcount
