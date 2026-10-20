"""Measure verdict accuracy and latency on the labelled datasets and write eval/report.md.

    cd kavach/backend
    python ../eval/evaluate.py                       # uses whatever LLM / API keys are in backend/.env
    NETWORK_CHECKS=0 python ../eval/evaluate.py      # offline: rules + lookalike links only
    python ../eval/evaluate.py --write-demo-cache    # also rebuild data/samples/demo_cache.json

Three sets are reported separately:
  sealed       heldout2.jsonl: written and sealed BEFORE the last rule changes; never tune on it
  held-out 1   heldout.jsonl: unseen at first (recall 0.13), then used to generalise the rules,
               so it is now development data
  development  scams.jsonl + legit.jsonl: the rules were written while looking at these

Auditability: DEMO_MODE is forced off while evaluating (cached answers would make the
numbers circular), the demo cache is built from the development set only (never from a
held-out set), and every run writes per-message results to eval/results/ plus the SHA-256
of each dataset file and the git commit into the report.
"""
import argparse
import asyncio
import hashlib
import json
import platform
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from kavach.analysis import bait, blocklist, ocr, scam_check   # noqa: E402
from kavach.analysis.settings import settings                         # noqa: E402
from kavach.analysis.models import AnalysisRequest               # noqa: E402

SAMPLES = ROOT / "data" / "samples"
sys.path.insert(0, str(ROOT / "eval"))
import dashboard                                           # noqa: E402
RESULTS = ROOT / "eval" / "results"
SETS = {"sealed_v3": ["heldout3.jsonl"], "sealed": ["heldout2.jsonl"], "sealed_calls": ["heldout_calls.jsonl"], "heldout1": ["heldout.jsonl"],
        "development": ["scams.jsonl", "legit.jsonl"]}
INPUT_TYPE = {"sealed_calls": "transcript"}               # spoken Call Shield transcripts; the rest are text


def load(names: list[str]) -> list[dict]:
    rows = []
    for name in names:
        rows += [json.loads(l) for l in (SAMPLES / name).read_text("utf-8").splitlines() if l.strip()]
    return rows


def sha256_file(name: str) -> str:
    # Line endings normalised: a Windows checkout (CRLF) and Linux (LF) give the same fingerprint.
    return hashlib.sha256((SAMPLES / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


PACE_S = 0.0     # seconds between messages; --pace keeps a free-tier LLM under its requests-per-minute limit


async def run(rows: list[dict], input_type: str = "text") -> list[dict]:
    out = []
    for row in rows:
        if PACE_S and out:
            await asyncio.sleep(PACE_S)                     # not counted in latency
        t0 = time.perf_counter()
        r = await scam_check.analyze(AnalysisRequest(request_id=row["id"], channel="web",
                                                     input_type=input_type, text=row["text"]))
        ms = (time.perf_counter() - t0) * 1000              # sub-millisecond precision
        out.append({**row, "score": r.risk_score, "level": r.risk_level, "pred_type": r.scam_type.value,
                    "latency_ms": ms, "confidence": r.confidence, "result": r.model_dump(mode="json")})
    return out


async def demo_input_results() -> dict[str, dict]:
    """Verdicts for data/samples/demo_inputs.jsonl (the items prepared on the demo phone)."""
    out = {}
    for row in load(["demo_inputs.jsonl"]):
        req = AnalysisRequest(request_id=row["id"], channel="whatsapp", input_type="text", text=row["text"])
        r = await (bait.verify(req) if row["kind"] == "bait" else scam_check.analyze(req))
        out[scam_check.demo_cache_key(row["text"], row["kind"])] = r.model_dump(mode="json")
    return out


def metrics(res: list[dict], medium: int) -> dict:
    scams = [x for x in res if x["label"] == "scam"]
    legit = [x for x in res if x["label"] == "legit"]
    tp = sum(x["score"] >= medium for x in scams)
    fp = sum(x["score"] >= medium for x in legit)
    return {"recall": tp / len(scams), "precision": tp / (tp + fp) if tp + fp else 0.0,
            "false_alarms": fp, "legit_total": len(legit), "tp": tp, "scam_total": len(scams)}


def pct(values: list[float], q: float) -> float:
    s = sorted(values)
    return s[min(len(s) - 1, round(q * (len(s) - 1)))]


def section(title: str, res: list[dict], sweep: bool) -> list[str]:
    med = scam_check.MEDIUM
    m = metrics(res, med)
    lat = [x["latency_ms"] for x in res]
    llm_answered = sum(x["confidence"] == "normal" for x in res)
    scams = [x for x in res if x["label"] == "scam"]
    type_ok = sum(x["pred_type"] == x["scam_type"] for x in scams if x["score"] >= med)
    by_lang = defaultdict(lambda: [0, 0])
    for x in scams:
        by_lang[x["language"]][0] += x["score"] >= med
        by_lang[x["language"]][1] += 1
    misses = [x for x in scams if x["score"] < med]
    alarms = [x for x in res if x["label"] == "legit" and x["score"] >= med]
    yes = lambda ok: "yes" if ok else "**no**"
    lines = [
        f"## {title}", "",
        f"{m['scam_total']} scam + {m['legit_total']} legitimate messages. "
        f"LLM verdict used for {llm_answered} of {len(res)} messages.", "",
        "| Metric | Value | Target (guide) | Met? |", "| --- | --- | --- | --- |",
        f"| Recall on scams | {m['recall']:.2f} ({m['tp']}/{m['scam_total']}) | ≥ 0.85 | {yes(m['recall'] >= 0.85)} |",
        f"| False alarms on legit | {m['false_alarms']} of {m['legit_total']} | ≤ 10% | "
        f"{yes(m['false_alarms'] <= 0.1 * m['legit_total'])} |",
        f"| Precision | {m['precision']:.2f} | n/a | |",
        f"| Median latency | {statistics.median(lat):.2f} ms | ≤ 6000 ms | {yes(statistics.median(lat) <= 6000)} |",
        f"| p95 / max latency | {pct(lat, 0.95):.2f} / {max(lat):.2f} ms | n/a | |",
        f"| Scam-type accuracy (flagged scams) | {type_ok}/{m['tp']} | n/a | |", "",
        "| Language | Scams flagged | Total |", "| --- | --- | --- |",
        *[f"| {k} | {v[0]} | {v[1]} |" for k, v in sorted(by_lang.items())], "",
    ]
    if sweep:
        lines += ["Threshold sweep (medium cut-off):", "", "| Medium ≥ | Recall | False alarms |", "| --- | --- | --- |",
                  *[f"| {t} | {metrics(res, t)['recall']:.2f} | {metrics(res, t)['false_alarms']} |"
                    for t in (25, 30, 35, 40, 50)], ""]
    lines += ["Missed scams:", "",
              *([f"- `{x['id']}` ({x['scam_type']}, {x['language']}, score {x['score']}): {x['text'][:90]}..."
                 for x in misses] or ["- none"]), "",
              "False alarms:", "",
              *([f"- `{x['id']}` (score {x['score']}): {x['text'][:90]}" for x in alarms] or ["- none"]), ""]
    return lines


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def services() -> list[str]:
    """What was actually enabled for this run. Never prints keys."""
    online = settings.NETWORK_CHECKS
    llm_on = bool(settings.LLM_BASE_URL and settings.LLM_MODEL)
    llm_host = (urlsplit(settings.LLM_BASE_URL).hostname or "?") if llm_on else ""
    try:
        ocr._langs()
        ocr_state = "installed (not used: all eval inputs are text)"
    except Exception:
        ocr_state = "not installed (not used: all eval inputs are text)"
    commit = _git("rev-parse", "--short", "HEAD") or "unknown"
    dirty = " + uncommitted changes" if _git("status", "--porcelain") else ""
    on_off = lambda b: "**on**" if b else "off"
    return [
        "## Run configuration", "",
        "| Component | State for this run |", "| --- | --- |",
        f"| Code version | git `{commit}`{dirty} |",
        f"| LLM classifier | {on_off(llm_on)}" + (f" (`{settings.LLM_MODEL}` at `{llm_host}`)" if llm_on else
                                              " (no LLM_BASE_URL / LLM_MODEL): rules + links only") + " |",
        f"| Network reputation checks (`NETWORK_CHECKS`) | {on_off(online)} |",
        f"| Google Safe Browsing | {on_off(online and bool(settings.SAFE_BROWSING_KEY))} |",
        f"| VirusTotal URL lookup | {on_off(online and bool(settings.VT_API_KEY))} |",
        f"| WHOIS domain age | {on_off(online)} |",
        "| Lookalike-domain and suspicious-TLD checks | **on** (offline, always) |",
        f"| Local URLhaus blocklist | {on_off(bool(blocklist.hosts()))}"
        + (f" ({len(blocklist.hosts())} hosts)" if blocklist.hosts() else " (not downloaded)") + " |",
        f"| Tesseract OCR | {ocr_state} |",
        "| `DEMO_MODE` cache | off (forced off by the evaluator) |",
        f"| Thresholds | high ≥ {scam_check.HIGH}, medium ≥ {scam_check.MEDIUM}; 'flagged' = medium or high |",
        f"| Python | {platform.python_version()} on {platform.system()} |", "",
        "Latency is wall-clock time per `analyze()` call on this machine, measured with `time.perf_counter()`. "
        "With network checks and the LLM off it reflects only local rule and regex work; real WhatsApp "
        "latency will be dominated by the LLM and reputation APIs.", "",
        "Dataset fingerprints (SHA-256), so a later reader can confirm the files were not edited after this run:", "",
        *[f"- `{name}`: `{sha256_file(name)[:16]}…`" for names in SETS.values() for name in names], "",
    ]


def write_results(name: str, res: list[dict]) -> None:
    RESULTS.mkdir(exist_ok=True)
    keep = ("id", "label", "scam_type", "language", "pred_type", "score", "level", "confidence")
    with open(RESULTS / f"{name}.jsonl", "w", encoding="utf-8") as f:
        for x in res:
            f.write(json.dumps({**{k: x[k] for k in keep}, "latency_ms": round(x["latency_ms"], 3)}) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--write-demo-cache", action="store_true",
                   help="rebuild data/samples/demo_cache.json from the development set only")
    p.add_argument("--pace", type=float, default=0.0, metavar="SECONDS",
                   help="wait between messages, e.g. 2.2 for a 30-requests-per-minute LLM tier")
    args = p.parse_args()
    global PACE_S
    PACE_S = args.pace

    settings.DEMO_MODE = False                               # cached answers would make the evaluation circular
    res = {name: asyncio.run(run(load(files), INPUT_TYPE.get(name, "text"))) for name, files in SETS.items()}
    lines = [
        "# Kavach Scam Check: evaluation report", "",
        f"Generated {datetime.now():%Y-%m-%d %H:%M} by `eval/evaluate.py`. Owner: Member 2. "
        "All phone numbers, UPI IDs and links in the datasets are fake.", "",
        "**Quote the newest sealed set on the slide** (`heldout3.jsonl`): it was committed before the last "
        "prompt and fusion changes and never used for tuning. Older sealed sets were seen by later changes "
        "(heldout2 and the call set informed the LLM calibration), and the development sets were used to write "
        "the rules, so their numbers are optimistic.", "",
        *services(),
        *section("Sealed test set 3 (`heldout3.jsonl`, committed before the LLM calibration)", res["sealed_v3"],
                 sweep=False),
        *section("Sealed test set 2 (`heldout2.jsonl`, never tuned on by the rules)", res["sealed"], sweep=False),
        *section("Sealed call transcripts (`heldout_calls.jsonl`, committed before the call-scam rules)",
                 res["sealed_calls"], sweep=False),
        "History: held-out set 1 scored recall **0.13** (2/15) on its first, honest run with the original "
        "keyword rules. That exposed overfitting and a URL bug; the rules were then generalised and the "
        "sealed set above was written before those changes.", "",
        *section("Held-out set 1 (`heldout.jsonl`, used for tuning after its first run)", res["heldout1"], sweep=False),
        *section("Development set (`scams.jsonl` + `legit.jsonl`)", res["development"], sweep=True),
        "## Caveats", "",
        "- Results for each message are in `eval/results/<set>.jsonl`.",
        "- Without an LLM key every verdict is `confidence: \"lower\"`. Re-run with the LLM configured and "
        "report both modes.",
        "- Tamil and Hindi keyword lists need review by a native speaker.",
        "- Small sets: one message changes recall by 2.5 to 7 points. Treat these as indicative.",
        "- One author wrote every set, including the sealed one; messages written by other team members "
        "would be a fairer test.", "",
    ]
    for name, r in res.items():
        write_results(name, r)
    (ROOT / "eval" / "report.md").write_text("\n".join(lines), encoding="utf-8")
    llm_on = bool(settings.LLM_BASE_URL and settings.LLM_MODEL)
    mode = (f"Mode: LLM ({settings.LLM_MODEL}) + rules + links" if llm_on else "Mode: rules + links, no LLM") \
        + ("; network checks on" if settings.NETWORK_CHECKS else "; offline (no network checks)")
    dashboard.build(scam_check.MEDIUM, scam_check.HIGH, mode)
    if args.write_demo_cache:
        # Development samples and the prepared demo inputs only: a held-out text in the cache could
        # leak into a DEMO_MODE run.
        cache = {x["text"]: x["result"] for x in res["development"]}
        cache.update(asyncio.run(demo_input_results()))
        (SAMPLES / "demo_cache.json").write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
