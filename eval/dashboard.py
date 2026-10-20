"""Build eval/dashboard.html (the guide's P2 "accuracy dashboard") from eval/results/*.jsonl.

    python eval/dashboard.py          # also run automatically at the end of eval/evaluate.py

One self-contained HTML file (no CDN, works offline at the venue): headline numbers per
dataset, every message's risk score against the medium/high thresholds, and a table view.
"""
import html
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"
SAMPLES = ROOT / "data" / "samples"
SETS = [  # (results file stem, label, dataset files, note)
    ("sealed_v3", "Sealed set 3", ["heldout3.jsonl"], "Newest sealed set: quote this one"),
    ("sealed", "Sealed text set", ["heldout2.jsonl"], "Never tuned on by the rules"),
    ("sealed_calls", "Sealed call transcripts", ["heldout_calls.jsonl"], "Spoken Call Shield text"),
    ("heldout1", "Held-out set 1", ["heldout.jsonl"], "Used for tuning after its first run"),
    ("development", "Development set", ["scams.jsonl", "legit.jsonl"], "Rules were written on it"),
]


def _texts() -> dict[str, str]:
    out = {}
    for _, _, files, _ in SETS:
        for name in files:
            for line in (SAMPLES / name).read_text("utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    out[row["id"]] = row["text"]
    return out


def collect(medium: int = 40) -> list[dict]:
    texts = _texts()
    sets = []
    for stem, label, _, note in SETS:
        path = RESULTS / f"{stem}.jsonl"
        if not path.exists():
            continue
        rows = [json.loads(l) for l in path.read_text("utf-8").splitlines() if l.strip()]
        for r in rows:
            r["text"] = texts.get(r["id"], "")[:140]
        scams = [r for r in rows if r["label"] == "scam"]
        legit = [r for r in rows if r["label"] == "legit"]
        sets.append({"key": stem, "label": label, "note": note, "rows": rows,
                     "tp": sum(r["score"] >= medium for r in scams), "scams": len(scams),
                     "fp": sum(r["score"] >= medium for r in legit), "legit": len(legit),
                     "llm": sum(r["confidence"] == "normal" for r in rows)})
    return sets


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kavach Accuracy Dashboard</title>
<style>
:root{color-scheme:light;--surface:#fcfcfb;--card:#ffffff;--text:#0b0b0b;--text2:#52514e;--muted:#8a8984;
 --line:#e4e3df;--grid:#efeeea;--scam:#2a78d6;--legit:#eb6834;--band:#f4f3ef}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--surface:#1a1a19;--card:#222221;
 --text:#f0efec;--text2:#c3c2b7;--muted:#8f8e86;--line:#3a3936;--grid:#2c2b29;--scam:#3987e5;--legit:#d95926;--band:#262624}}
:root[data-theme="dark"]{color-scheme:dark;--surface:#1a1a19;--card:#222221;--text:#f0efec;--text2:#c3c2b7;--muted:#8f8e86;
 --line:#3a3936;--grid:#2c2b29;--scam:#3987e5;--legit:#d95926;--band:#262624}
*{box-sizing:border-box}body{margin:0;background:var(--surface);color:var(--text);
 font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1040px;margin:0 auto;padding:28px 16px 48px}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.01em}h2{font-size:17px;margin:32px 0 6px}
.sub{color:var(--text2);margin:0 0 20px}.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.tile .k{color:var(--text2);font-size:13px}.tile .v{font-size:30px;font-weight:650;letter-spacing:-.02em;margin:2px 0}
.tile .v small{font-size:15px;font-weight:500;color:var(--text2)}.tile .n{color:var(--muted);font-size:12.5px}
.ok{color:var(--text2)}.legend{display:flex;gap:18px;color:var(--text2);font-size:13px;margin:6px 0 4px;flex-wrap:wrap}
.legend span{display:inline-flex;align-items:center;gap:6px}.card{background:var(--card);border:1px solid var(--line);
 border-radius:12px;padding:12px 12px 4px;overflow-x:auto}svg{display:block;width:100%;min-width:560px;height:auto}
.tip{position:fixed;pointer-events:none;background:var(--card);color:var(--text);border:1px solid var(--line);
 border-radius:8px;padding:8px 10px;font-size:12.5px;max-width:320px;box-shadow:0 4px 16px rgba(0,0,0,.12);display:none;z-index:5}
.tip b{font-weight:600}.tip .m{color:var(--text2)}table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--text2);font-weight:600}
td.num{text-align:right;font-variant-numeric:tabular-nums}details{margin-top:10px}summary{cursor:pointer;color:var(--text2)}
.foot{color:var(--muted);font-size:12.5px;margin-top:28px}
</style></head><body><main>
<h1>Kavach analysis engine: accuracy</h1>
<p class="sub">__MODE__ · thresholds: medium ≥ __MED__, high ≥ __HIGH__ · generated __WHEN__ from <code>eval/results/</code></p>
<div class="tiles">__TILES__</div>
<h2>Every message's risk score</h2>
<p class="sub" style="margin:0">Scams should sit right of the medium line, genuine messages left of it. Hover a mark for the message.</p>
<div class="legend"><span><svg width="12" height="12" style="min-width:0"><circle cx="6" cy="6" r="5" fill="var(--scam)"/></svg>Scam</span>
<span><svg width="12" height="12" style="min-width:0"><rect x="1.5" y="1.5" width="9" height="9" fill="none" stroke="var(--legit)" stroke-width="2"/></svg>Genuine</span></div>
<div class="card"><svg id="strip" role="img" aria-label="Risk score of every message per dataset"></svg></div>
<details><summary>Table view: every message</summary><table>__TABLE__</table></details>
<h2>Misses and false alarms</h2>
<table><thead><tr><th>Set</th><th>ID</th><th>Expected</th><th class="num">Score</th><th>Message</th></tr></thead><tbody>__MISSES__</tbody></table>
<p class="foot">Offline numbers are rules + link checks only unless the mode line above says the LLM was on. Test sets are small and
written by the team: one message moves recall by 7 points. See docs/LIMITATIONS.md.</p>
</main><div class="tip" id="tip"></div>
<script type="application/json" id="data">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent), MED = __MED__, HIGH = __HIGH__;
const svg = document.getElementById('strip'), NS = 'http://www.w3.org/2000/svg', tip = document.getElementById('tip');
const W = 960, L = 268, R = 30, rowH = 64, top = 26, H = top + D.length * rowH + 28;
svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
const x = s => L + 10 + (W - L - R - 10) * s / 100;
const el = (n, a, p = svg) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); p.appendChild(e); return e; };
el('rect', {x: x(MED), y: top - 6, width: x(100) - x(MED), height: D.length * rowH, fill: 'var(--band)'});
for (const t of [0, 20, 40, 60, 80, 100]) {
  el('line', {x1: x(t), x2: x(t), y1: top - 6, y2: top + D.length * rowH, stroke: 'var(--grid)', 'stroke-width': 1});
  el('text', {x: x(t), y: H - 8, 'text-anchor': 'middle', 'font-size': 12, fill: 'var(--muted)'}).textContent = t;
}
for (const [t, name] of [[MED, 'medium'], [HIGH, 'high']]) {
  el('line', {x1: x(t), x2: x(t), y1: top - 10, y2: top + D.length * rowH, stroke: 'var(--text2)', 'stroke-width': 1.5, 'stroke-dasharray': '4 3'});
  el('text', {x: x(t) + 4, y: top - 12, 'font-size': 12, fill: 'var(--text2)'}).textContent = `${name} ≥ ${t}`;
}
D.forEach((set, i) => {
  const cy = top + i * rowH + rowH / 2;
  el('text', {x: 0, y: cy - 4, 'font-size': 13.5, 'font-weight': 600, fill: 'var(--text)'}).textContent = set.label;
  el('text', {x: 0, y: cy + 13, 'font-size': 12, fill: 'var(--muted)'}).textContent = set.note;
  const seen = {}, piles = {};
  set.rows.forEach(r => {
    const k = Math.round(r.score / 2.5), n = (seen[k + r.label] = (seen[k + r.label] || 0) + 1);
    piles[k + r.label] = {n, score: r.score, label: r.label};
    const off = (r.label === 'scam' ? -1 : 1) * (6 + ((n - 1) % 3) * 7);
    const g = el('g', {tabindex: 0});
    const cx = x(r.score), y = cy + off;
    if (r.label === 'scam') el('circle', {cx, cy: y, r: 5, fill: 'var(--scam)', stroke: 'var(--card)', 'stroke-width': 2}, g);
    else el('rect', {x: cx - 4.5, y: y - 4.5, width: 9, height: 9, fill: 'var(--card)', stroke: 'var(--legit)', 'stroke-width': 2}, g);
    el('circle', {cx, cy: y, r: 11, fill: 'transparent'}, g);   // larger hit target
    const show = ev => { const p = ev.touches ? ev.touches[0] : ev;
      tip.innerHTML = `<b>${r.id}</b> · ${r.label === 'scam' ? 'scam (' + r.scam_type + ')' : 'genuine'}<br>`
        + `score <b>${r.score}</b> → ${r.level}${r.label === 'scam' ? ', predicted ' + r.pred_type : ''}<br><span class="m">${esc(r.text)}</span>`;
      tip.style.display = 'block'; tip.style.left = Math.min(p.clientX + 14, innerWidth - 330) + 'px'; tip.style.top = (p.clientY + 14) + 'px'; };
    g.addEventListener('mousemove', show); g.addEventListener('focus', e => { const b = g.getBoundingClientRect(); show({clientX: b.right, clientY: b.top}); });
    g.addEventListener('mouseleave', () => tip.style.display = 'none'); g.addEventListener('blur', () => tip.style.display = 'none');
  });
  // More than 3 identical scores stack on top of each other: print the count so none are hidden.
  for (const p of Object.values(piles)) if (p.n > 3) {
    const sign = p.label === 'scam' ? -1 : 1;
    el('text', {x: x(p.score) + 9, y: cy + sign * 20 + 4, 'font-size': 11.5, fill: 'var(--text2)'}).textContent = `×${p.n}`;
  }
});
function esc(s) { return s.replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c])); }
</script></body></html>
"""


def build(medium: int = 40, high: int = 70, mode: str = "") -> Path:
    sets = collect(medium)
    tiles = "".join(
        f'<div class="tile"><div class="k">{html.escape(s["label"])}</div>'
        f'<div class="v">{s["tp"] / s["scams"]:.2f} <small>recall</small></div>'
        f'<div class="n">{s["tp"]}/{s["scams"]} scams caught · {s["fp"]} of {s["legit"]} genuine flagged · '
        f'LLM used on {s["llm"]}/{len(s["rows"])}</div></div>' for s in sets)
    rows_html = ["<thead><tr><th>Set</th><th>ID</th><th>Label</th><th class='num'>Score</th><th>Level</th>"
                 "<th>Predicted type</th><th>Message</th></tr></thead><tbody>"]
    misses = []
    for s in sets:
        for r in s["rows"]:
            cells = (f"<td>{html.escape(s['label'])}</td><td>{r['id']}</td><td>{r['label']}</td>"
                     f"<td class='num'>{r['score']}</td><td>{r['level']}</td><td>{r['pred_type']}</td>"
                     f"<td>{html.escape(r['text'])}</td>")
            rows_html.append(f"<tr>{cells}</tr>")
            wrong = (r["label"] == "scam") != (r["score"] >= medium)
            if wrong:
                kind = r["scam_type"] if r["label"] == "scam" else "genuine (false alarm)"
                misses.append(f"<tr><td>{html.escape(s['label'])}</td><td>{r['id']}</td><td>{kind}</td>"
                              f"<td class='num'>{r['score']}</td><td>{html.escape(r['text'])}</td></tr>")
    rows_html.append("</tbody>")
    data = [{"key": s["key"], "label": s["label"], "note": s["note"], "rows": s["rows"]} for s in sets]
    page = (PAGE.replace("__MODE__", html.escape(mode or "Mode: see eval/report.md"))
            .replace("__MED__", str(medium)).replace("__HIGH__", str(high))
            .replace("__WHEN__", datetime.now().strftime("%Y-%m-%d %H:%M"))
            .replace("__TILES__", tiles).replace("__TABLE__", "".join(rows_html))
            .replace("__MISSES__", "".join(misses) or "<tr><td colspan='5'>None</td></tr>")
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    out = ROOT / "eval" / "dashboard.html"
    out.write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(build(mode=" ".join(sys.argv[1:])))
