"""Local URL blocklist from the abuse.ch URLhaus feed (guide section 3, "Optional").

Works offline once downloaded, so a known malware or phishing host is flagged even when
Safe Browsing and VirusTotal keys are missing or the venue Wi-Fi is down.

    python -m kavach.analysis.blocklist --update      # run once at setup / before the demo

Only hostnames are stored, in a git-ignored file (default backend/data/blocklists/
urlhaus_hosts.txt), so no live malicious links ever enter the repository. PhishTank now
requires a registered application key, so it is not included.
"""
import argparse
import csv
import io
import sys
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from kavach.analysis.settings import BACKEND_DIR, settings

URLHAUS_ONLINE_CSV = "https://urlhaus.abuse.ch/downloads/csv_online/"
DEFAULT_PATH = BACKEND_DIR / "data" / "blocklists" / "urlhaus_hosts.txt"


def path() -> Path:
    return Path(settings.BLOCKLIST_PATH) if settings.BLOCKLIST_PATH else DEFAULT_PATH


def parse_urlhaus_csv(text: str) -> set[str]:
    """Hostnames from a URLhaus CSV export (comment lines start with '#')."""
    rows = csv.reader(io.StringIO("\n".join(l for l in text.splitlines() if l and not l.startswith("#"))))
    hosts = set()
    for row in rows:
        if len(row) > 2:
            host = (urlsplit(row[2].strip()).hostname or "").lower().rstrip(".")
            if host and not host.replace(".", "").isdigit():  # skip bare IPs: they rotate too fast
                hosts.add(host)
    return hosts


@lru_cache(maxsize=1)
def hosts() -> frozenset[str]:
    try:
        return frozenset(l.strip() for l in path().read_text("utf-8").splitlines() if l.strip())
    except OSError:
        return frozenset()                                  # not downloaded: the check is simply skipped


def is_blocklisted(domain: str) -> bool:
    domain = domain.lower().rstrip(".")
    listed = hosts()
    return domain in listed or any(domain.endswith("." + h) for h in listed if h.count(".") >= 1)


def update(timeout: float = 60) -> int:
    r = httpx.get(URLHAUS_ONLINE_CSV, timeout=timeout, follow_redirects=True)
    r.raise_for_status()
    found = parse_urlhaus_csv(r.text)
    if not found:
        raise RuntimeError("URLhaus returned no hosts; keeping the existing list")
    target = path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(sorted(found)) + "\n", encoding="utf-8")
    hosts.cache_clear()
    return len(found)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Manage the local URLhaus host blocklist")
    p.add_argument("--update", action="store_true", help="download the current online URLhaus list")
    a = p.parse_args(argv)
    if a.update:
        print(f"saved {update()} hosts to {path()}")
    else:
        print(f"{len(hosts())} hosts in {path()}" if hosts() else f"no blocklist at {path()}; run with --update")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
