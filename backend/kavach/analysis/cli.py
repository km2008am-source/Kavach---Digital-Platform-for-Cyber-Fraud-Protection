"""Command-line demo of Member 2's engine, for testing and the jury Q&A (no WhatsApp or web needed).

    python -m kavach.analysis.cli "Your SBI account will be blocked today. Share OTP"
    python -m kavach.analysis.cli --apk ../data/samples/apks/rto_challan_test.apk
    python -m kavach.analysis.cli --image screenshot.png
    python -m kavach.analysis.cli --bait "PM Free Laptop Yojana, register at pm-laptop.site"
    python -m kavach.analysis.cli --receipt receipt1.png receipt2.png
    python -m kavach.analysis.cli --pulse-replay
    python -m kavach.analysis.cli --json "..."      # raw AnalysisResult JSON (what M1 / M3 receive)
"""
import argparse
import asyncio
import sys
import uuid

from kavach.analysis import bait, evidence, links, pulse, scam_check
from kavach.analysis.models import AnalysisRequest, AnalysisResult

ICON = {"high": "HIGH RISK", "medium": "MEDIUM RISK", "low": "LOW RISK"}


def show(r: AnalysisResult) -> None:
    print(f"\n  {ICON[r.risk_level]}  score {r.risk_score}/100  type: {r.scam_type.value}  "
          f"confidence: {r.confidence}  ({r.latency_ms} ms)")
    print(f"  {r.explanation_en}")
    for f in r.red_flags:
        print(f"   - [{f.code}] {f.label_en}")
    for link in r.links:
        notes = [f"looks like {link.lookalike_of}" if link.lookalike_of else "",
                 "cheap scam-prone address" if links.suspicious_tld(link.domain) else "",
                 "BLOCKLISTED" if link.blocklisted else "",
                 f"{link.domain_age_days} days old" if link.domain_age_days is not None else ""]
        print(f"   link {link.domain}: {', '.join(n for n in notes if n) or 'no issues found'}")
    if r.apk:
        print(f"   app: {r.apk.app_name} ({r.apk.package}), dangerous combo: {r.apk.dangerous_combo}")
        print(f"   permissions: {', '.join(p.rsplit('.', 1)[-1] for p in r.apk.permissions) or 'none'}")
    print(f"  Recommended action: {r.recommended_action}\n")


def req(input_type: str, text: str = "", path: str | None = None) -> AnalysisRequest:
    return AnalysisRequest(request_id=uuid.uuid4().hex[:8], channel="web", input_type=input_type,
                           text=text, file_path=path)


async def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="kavach-check", description="Kavach scam check (Member 2 engine)")
    p.add_argument("text", nargs="?", help="message text or link to check")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--apk", metavar="PATH")
    g.add_argument("--image", metavar="PATH")
    g.add_argument("--bait", metavar="POST", help="forwarded news / scheme post")
    g.add_argument("--receipt", metavar="PATH", nargs="+", help="payment receipt images (Golden Hour)")
    g.add_argument("--pulse-replay", action="store_true", help="insert seed reports and print alerts")
    p.add_argument("--json", action="store_true", help="print raw JSON")
    a = p.parse_args(argv)

    if a.pulse_replay:
        print(f"inserted {pulse.replay()} seed reports")
        for alert in pulse.alerts():
            print(alert.model_dump_json(indent=2) if a.json else
                  f"  [{alert.confidence}] {alert.district}: {alert.label}, "
                  f"{alert.report_count} reports from {alert.distinct_reporters} people")
        return 0
    if a.receipt:
        print((await evidence.extract_evidence(a.receipt)).model_dump_json(indent=2))
        return 0
    if a.apk:
        r = await scam_check.analyze(req("apk", path=a.apk))
    elif a.image:
        r = await scam_check.analyze(req("image", a.text or "", a.image))
    elif a.bait:
        r = await bait.verify(req("text", a.bait))
    elif a.text:
        r = await scam_check.analyze(req("text", a.text))
    else:
        p.print_help()
        return 2
    print(r.model_dump_json(indent=2)) if a.json else show(r)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")            # Tamil text on Windows consoles
    sys.exit(asyncio.run(main(sys.argv[1:])))
