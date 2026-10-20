import httpx
import pytest
import respx

from kavach.analysis import links
from kavach.analysis.settings import settings


@pytest.mark.parametrize("domain, expected", [
    ("sbi-kyc-update.xyz", "sbi.co.in"),
    ("onlinesbi.sbi", None),
    ("amazon.in", None),
    ("www.hdfc-pan-verify.top", "hdfcbank.com"),
    ("kyc-indianbank.online", "indianbank.in"),
    ("hdfcbnak.com", "hdfcbank.com"),            # typo-squat
    ("uidai.gov.in", None),
    ("google.com", None),
])
def test_lookalike(domain, expected):
    assert links.lookalike(domain) == expected


def test_suspicious_tld():
    assert links.suspicious_tld("rto-echallan-pay.xyz")
    assert not links.suspicious_tld("parivahan.gov.in")


async def test_check_links_offline_still_flags_lookalike():
    [check] = await links.check_links(["http://sbi-kyc-update.xyz/login"])
    assert check.domain == "sbi-kyc-update.xyz"
    assert check.lookalike_of == "sbi.co.in"
    assert check.blocklisted is False and check.domain_age_days is None


@respx.mock
async def test_safe_browsing_hit_marks_blocklisted(monkeypatch):
    monkeypatch.setattr(settings, "NETWORK_CHECKS", True)
    monkeypatch.setattr(settings, "SAFE_BROWSING_KEY", "k")
    monkeypatch.setattr(links, "domain_age_days", lambda d: _async(None))
    url = "http://bad-site.xyz/x"
    respx.post(url__startswith="https://safebrowsing.googleapis.com").mock(
        return_value=httpx.Response(200, json={"matches": [{"threat": {"url": url}}]}))
    [check] = await links.check_links([url])
    assert check.blocklisted and check.sources == ["safe_browsing"]


@respx.mock
async def test_failing_source_never_blocks_the_verdict(monkeypatch):
    monkeypatch.setattr(settings, "NETWORK_CHECKS", True)
    monkeypatch.setattr(settings, "SAFE_BROWSING_KEY", "k")
    monkeypatch.setattr(settings, "VT_API_KEY", "k")
    monkeypatch.setattr(links, "domain_age_days", lambda d: _async(None))
    respx.post(url__startswith="https://safebrowsing.googleapis.com").mock(side_effect=httpx.ConnectTimeout("x"))
    respx.get(url__startswith="https://www.virustotal.com").mock(return_value=httpx.Response(429))
    [check] = await links.check_links(["http://sbi-kyc-update.xyz/"])
    assert check.blocklisted is False and check.lookalike_of == "sbi.co.in"


async def _async(value):
    return value


# ---- local URLhaus blocklist (hostnames only; fake values in tests) ----

URLHAUS_SAMPLE = """################################################################
# abuse.ch URLhaus Database Dump (CSV - online URLs only)       #
################################################################
# id,dateadded,url,url_status,last_online,threat,tags,urlhaus_link,reporter
"1","2026-10-20 10:00:00","http://bad-payload.example-test.xyz/a.apk","online","2026-10-20","malware_download","apk","https://urlhaus.abuse.ch/url/1/","test"
"2","2026-10-20 10:01:00","https://cdn.evil-files.example-test.top/x","online","2026-10-20","malware_download","","https://urlhaus.abuse.ch/url/2/","test"
"3","2026-10-20 10:02:00","http://192.0.2.10/bin","online","2026-10-20","malware_download","","https://urlhaus.abuse.ch/url/3/","test"
"""


def test_parse_urlhaus_csv_keeps_hostnames_not_ips():
    from kavach.analysis.blocklist import parse_urlhaus_csv
    assert parse_urlhaus_csv(URLHAUS_SAMPLE) == {"bad-payload.example-test.xyz", "cdn.evil-files.example-test.top"}


async def test_local_blocklist_marks_link_blocklisted_offline(monkeypatch, tmp_path):
    from kavach.analysis import blocklist
    listfile = tmp_path / "hosts.txt"
    listfile.write_text("cdn.evil-files.example-test.top\n", encoding="utf-8")
    monkeypatch.setattr(settings, "BLOCKLIST_PATH", str(listfile))
    blocklist.hosts.cache_clear()
    try:
        [hit, sub, clean] = await links.check_links(["https://cdn.evil-files.example-test.top/x",
                                                     "http://a.cdn.evil-files.example-test.top/y",
                                                     "https://safe-site.example-test.org/"])
    finally:
        blocklist.hosts.cache_clear()
    assert hit.blocklisted and hit.sources == ["urlhaus"]
    assert sub.blocklisted                                   # subdomain of a listed host
    assert not clean.blocklisted


def test_missing_blocklist_file_is_skipped(monkeypatch, tmp_path):
    from kavach.analysis import blocklist
    monkeypatch.setattr(settings, "BLOCKLIST_PATH", str(tmp_path / "absent.txt"))
    blocklist.hosts.cache_clear()
    try:
        assert not blocklist.is_blocklisted("anything.xyz")
    finally:
        blocklist.hosts.cache_clear()
