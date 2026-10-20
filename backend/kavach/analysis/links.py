"""Reputation of every URL in a message: blocklists, lookalike brand domains, domain age.

Every network source is optional and fails independently: a missing key, a timeout or a
rate limit just removes that source, it never blocks the verdict. The offline checks
(lookalike + suspicious TLD) always run.
"""
import asyncio
import base64
import datetime as dt
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import tldextract
from rapidfuzz import fuzz

from kavach.analysis.settings import settings
from kavach.analysis.models import LinkCheck

# Bundled public-suffix snapshot: no network fetch at import time, works offline.
_extract = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)

BRANDS = [line.strip() for line in (Path(__file__).parent / "brand_domains.txt").read_text("utf-8").splitlines()
          if line.strip() and not line.startswith("#")]

# Cheap TLDs heavily used for throwaway phishing sites in Indian SMS campaigns.
SUSPICIOUS_TLDS = {"xyz", "top", "online", "site", "link", "info", "click", "buzz", "live", "shop", "icu"}

_cache: dict[str, LinkCheck] = {}          # session cache: VirusTotal's free tier is rate-limited
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
    return _client


def domain_of(url: str) -> str:
    if "://" not in url:
        url = "http://" + url
    return (urlsplit(url).hostname or "").lower().rstrip(".")


def registrable(domain: str) -> str:
    parts = _extract(domain)
    return f"{parts.domain}.{parts.suffix}" if parts.suffix else parts.domain


def suspicious_tld(domain: str) -> bool:
    return _extract(domain).suffix.split(".")[-1] in SUSPICIOUS_TLDS


def _brand_labels(brand: str) -> list[str]:
    label = _extract(brand).domain                       # "hdfcbank", "sbi", "indiapost"
    labels = [label]
    if label.endswith("bank") and len(label) > 6:       # "hdfc-pan-verify" impersonates hdfcbank.com
        labels.append(label[:-4])
    return labels


def lookalike(domain: str) -> str | None:
    """Return the official brand domain this domain imitates, or None."""
    if not domain:
        return None
    reg = registrable(domain)
    for b in BRANDS:
        if reg == b or domain == b or domain.endswith("." + b):
            return None                                   # it is the official domain
    name = _extract(domain).domain
    tokens = name.replace("_", "-").split("-")
    for b in BRANDS:
        for label in _brand_labels(b):
            if len(label) >= 3 and label in tokens:
                return b                                  # "sbi-kyc-update" contains "sbi"
            if len(label) >= 5 and (label in name or any(fuzz.ratio(label, t) >= 85 for t in tokens)):
                return b                                  # "kyc-indianbank", typo "hdfcbnak"
    return None


async def safe_browsing(urls: list[str]) -> set[str]:
    body = {"client": {"clientId": "kavach", "clientVersion": "0.1"},
            "threatInfo": {"threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                           "platformTypes": ["ANY_PLATFORM"], "threatEntryTypes": ["URL"],
                           "threatEntries": [{"url": u} for u in urls]}}
    r = await _get_client().post("https://safebrowsing.googleapis.com/v4/threatMatches:find",
                                 params={"key": settings.SAFE_BROWSING_KEY}, json=body)
    r.raise_for_status()
    return {m["threat"]["url"] for m in r.json().get("matches", [])}


async def vt_url(url: str) -> int | None:
    uid = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    r = await _get_client().get(f"https://www.virustotal.com/api/v3/urls/{uid}",
                                headers={"x-apikey": settings.VT_API_KEY})
    if r.status_code != 200:
        return None                                       # 404 = never scanned; 429 = rate limited
    return int(r.json()["data"]["attributes"]["last_analysis_stats"]["malicious"])


def _whois_age(domain: str) -> int | None:
    import whois                                          # python-whois; blocking, so run in a thread
    created = whois.whois(domain).creation_date
    created = created[0] if isinstance(created, list) else created
    if not isinstance(created, dt.datetime):
        return None
    now = dt.datetime.now(created.tzinfo) if created.tzinfo else dt.datetime.now()
    return max(0, (now - created).days)


async def domain_age_days(domain: str, timeout: float = 4) -> int | None:
    try:
        return await asyncio.wait_for(asyncio.to_thread(_whois_age, domain), timeout)
    except Exception:
        return None                                       # WHOIS timeouts are common: skip, never block


async def _optional(coro, default):
    try:
        return await coro
    except Exception:
        return default


async def check_links(urls: list[str]) -> list[LinkCheck]:
    urls = [u for u in dict.fromkeys(urls) if u][:5]      # cap work per message
    todo = [u for u in urls if u not in _cache]
    if todo:
        online = settings.NETWORK_CHECKS
        sb_task = _optional(safe_browsing(todo), set()) if online and settings.SAFE_BROWSING_KEY else None
        domains = [domain_of(u) for u in todo]
        vt_tasks = [_optional(vt_url(u), None) if online and settings.VT_API_KEY else None for u in todo]
        age_tasks = [domain_age_days(registrable(d)) if online and d and not _is_official(d) else None
                     for d in domains]
        results = await asyncio.gather(sb_task or _none(set()),
                                       *[t or _none(None) for t in vt_tasks],
                                       *[t or _none(None) for t in age_tasks])
        sb_hits, vt_hits, ages = results[0], results[1:1 + len(todo)], results[1 + len(todo):]
        for u, d, vt, age in zip(todo, domains, vt_hits, ages, strict=True):
            sources = (["safe_browsing"] if u in sb_hits else []) + (["virustotal"] if vt else [])
            _cache[u] = LinkCheck(url=u, domain=d, blocklisted=bool(sources), sources=sources,
                                  lookalike_of=lookalike(d), domain_age_days=age)
    return [_cache[u] for u in urls]


def _is_official(domain: str) -> bool:
    reg = registrable(domain)
    return any(reg == b or domain.endswith("." + b) for b in BRANDS)


async def _none(value):
    return value
