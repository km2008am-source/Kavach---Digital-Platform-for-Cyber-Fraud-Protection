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
