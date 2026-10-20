# Kavach Scam Check: evaluation report

Generated 2026-10-20 20:29 by `eval/evaluate.py`. Owner: Member 2. All phone numbers, UPI IDs and links in the datasets are fake.

**Quote the sealed-set numbers on the slide.** It was written before the last rule changes and was never used for tuning. The other two sets were used to write the rules, so their numbers are optimistic.

## Run configuration

| Component | State for this run |
| --- | --- |
| Code version | git `746de7f` + uncommitted changes |
| LLM classifier | off (no LLM_BASE_URL / LLM_MODEL): rules + links only |
| Network reputation checks (`NETWORK_CHECKS`) | off |
| Google Safe Browsing | off |
| VirusTotal URL lookup | off |
| WHOIS domain age | off |
| Lookalike-domain and suspicious-TLD checks | **on** (offline, always) |
| Local URLhaus blocklist | **on** (593 hosts) |
| Tesseract OCR | installed (not used: all eval inputs are text) |
| `DEMO_MODE` cache | off (forced off by the evaluator) |
| Thresholds | high ≥ 70, medium ≥ 40; 'flagged' = medium or high |
| Python | 3.14.3 on Windows |

Latency is wall-clock time per `analyze()` call on this machine, measured with `time.perf_counter()`. With network checks and the LLM off it reflects only local rule and regex work; real WhatsApp latency will be dominated by the LLM and reputation APIs.

Dataset fingerprints (SHA-256), so a later reader can confirm the files were not edited after this run:

- `heldout2.jsonl`: `490832e45e21225b…`
- `heldout_calls.jsonl`: `ee741aebc4495279…`
- `heldout.jsonl`: `105a84917a29f9b8…`
- `scams.jsonl`: `3832e6f9f881605a…`
- `legit.jsonl`: `9c12a0b6c71fd11f…`

## Sealed test set (`heldout2.jsonl`, never tuned on)

15 scam + 10 legitimate messages. LLM verdict used for 0 of 25 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 0.87 (13/15) | ≥ 0.85 | yes |
| False alarms on legit | 0 of 10 | ≤ 10% | yes |
| Precision | 1.00 | n/a | |
| Median latency | 0.42 ms | ≤ 6000 ms | yes |
| p95 / max latency | 5.08 / 18.76 ms | n/a | |
| Scam-type accuracy (flagged scams) | 8/13 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 9 | 10 |
| hi | 1 | 2 |
| ta | 3 | 3 |

Missed scams:

- `k04` (job_offer, en, score 20): Earn 5000 to 15000 per day from your mobile. Simple rating tasks for hotels. Contact our c...
- `k14` (kyc_update, hi, score 35): Aapka bank khata block kar diya jayega. KYC ke liye is number par turant call karein aur O...

False alarms:

- none

## Sealed call transcripts (`heldout_calls.jsonl`, committed before the call-scam rules)

10 scam + 6 legitimate messages. LLM verdict used for 0 of 16 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 0.80 (8/10) | ≥ 0.85 | **no** |
| False alarms on legit | 0 of 6 | ≤ 10% | yes |
| Precision | 1.00 | n/a | |
| Median latency | 0.42 ms | ≤ 6000 ms | yes |
| p95 / max latency | 0.51 / 0.76 ms | n/a | |
| Scam-type accuracy (flagged scams) | 8/8 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 6 | 8 |
| hi | 1 | 1 |
| ta | 1 | 1 |

Missed scams:

- `c04` (kyc_update, en, score 15): this call is from your bank fraud department your atm card will be blocked in thirty minut...
- `c05` (digital_arrest, en, score 15): this is trai your mobile number will be disconnected in two hours because complaints were ...

False alarms:

- none

History: held-out set 1 scored recall **0.13** (2/15) on its first, honest run with the original keyword rules. That exposed overfitting and a URL bug; the rules were then generalised and the sealed set above was written before those changes.

## Held-out set 1 (`heldout.jsonl`, used for tuning after its first run)

15 scam + 10 legitimate messages. LLM verdict used for 0 of 25 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 0.87 (13/15) | ≥ 0.85 | yes |
| False alarms on legit | 0 of 10 | ≤ 10% | yes |
| Precision | 1.00 | n/a | |
| Median latency | 0.44 ms | ≤ 6000 ms | yes |
| p95 / max latency | 0.78 / 0.83 ms | n/a | |
| Scam-type accuracy (flagged scams) | 8/13 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 9 | 10 |
| hi | 2 | 2 |
| ta | 2 | 3 |

Missed scams:

- `h04` (job_offer, en, score 20): Hi! I'm Priya from a recruitment agency. We have a part time role, 20 minutes a day, salar...
- `h13` (job_offer, ta, score 20): யூடியூப் வீடியோக்களை லைக் செய்து ஒவ்வொரு நாளும் வருமானம் பெறுங்கள். ஆர்வம் இருந்தால் இந்த ...

False alarms:

- none

## Development set (`scams.jsonl` + `legit.jsonl`)

40 scam + 20 legitimate messages. LLM verdict used for 0 of 60 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 0.93 (37/40) | ≥ 0.85 | yes |
| False alarms on legit | 0 of 20 | ≤ 10% | yes |
| Precision | 1.00 | n/a | |
| Median latency | 0.45 ms | ≤ 6000 ms | yes |
| p95 / max latency | 0.68 / 0.72 ms | n/a | |
| Scam-type accuracy (flagged scams) | 36/37 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 25 | 27 |
| hi | 3 | 3 |
| ta | 9 | 10 |

Threshold sweep (medium cut-off):

| Medium ≥ | Recall | False alarms |
| --- | --- | --- |
| 25 | 0.97 | 0 |
| 30 | 0.97 | 0 |
| 35 | 0.97 | 0 |
| 40 | 0.93 | 0 |
| 50 | 0.75 | 0 |

Missed scams:

- `s17` (job_offer, en, score 35): Part-time job! Work from home and earn daily Rs 3000 by liking YouTube videos. No experien...
- `s18` (job_offer, en, score 20): Congratulations, you are selected for Amazon data entry job. Salary Rs 45,000. Pay refunda...
- `s29` (investment, ta, score 35): பங்குச் சந்தையில் ஒரு மாதத்தில் இரட்டிப்பு லாபம் உறுதி. எங்கள் வாட்ஸ்அப் குழுவில் சேர்ந்து...

False alarms:

- none

## Caveats

- Results for each message are in `eval/results/<set>.jsonl`.
- Without an LLM key every verdict is `confidence: "lower"`. Re-run with the LLM configured and report both modes.
- Tamil and Hindi keyword lists need review by a native speaker.
- Small sets: one message changes recall by 2.5 to 7 points. Treat these as indicative.
- One author wrote every set, including the sealed one; messages written by other team members would be a fairer test.
