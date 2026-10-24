# Kavach Scam Check: evaluation report

Generated 2026-10-24 22:49 by `eval/evaluate.py`. Owner: Member 2. All phone numbers, UPI IDs and links in the datasets are fake.

**Quote the newest sealed set on the slide** (`heldout3.jsonl`): it was committed before the last prompt and fusion changes and never used for tuning. Older sealed sets were seen by later changes (heldout2 and the call set informed the LLM calibration), and the development sets were used to write the rules, so their numbers are optimistic.

## Run configuration

| Component | State for this run |
| --- | --- |
| Code version | git `5673a55` + uncommitted changes |
| LLM classifier | **on** (`openai/gpt-oss-120b` at `api.groq.com`) |
| Network reputation checks (`NETWORK_CHECKS`) | **on** |
| Google Safe Browsing | off |
| VirusTotal URL lookup | off |
| WHOIS domain age | **on** |
| Lookalike-domain and suspicious-TLD checks | **on** (offline, always) |
| Local URLhaus blocklist | **on** (593 hosts) |
| Tesseract OCR | not installed (not used: all eval inputs are text) |
| `DEMO_MODE` cache | off (forced off by the evaluator) |
| Thresholds | high ≥ 70, medium ≥ 40; 'flagged' = medium or high |
| Python | 3.14.3 on Windows |

Latency is wall-clock time per `analyze()` call on this machine, measured with `time.perf_counter()`. With network checks and the LLM off it reflects only local rule and regex work; real WhatsApp latency will be dominated by the LLM and reputation APIs.

Dataset fingerprints (SHA-256), so a later reader can confirm the files were not edited after this run:

- `heldout_hindi.jsonl`: `8cb42205ad315aed…`
- `heldout3.jsonl`: `63ffddacc34cd13f…`
- `heldout2.jsonl`: `f51be6e6b2dba3fb…`
- `heldout_calls.jsonl`: `400eccdf8e8d778a…`
- `heldout.jsonl`: `464a7c5aaa72b051…`
- `scams.jsonl`: `940588b2585e10cb…`
- `legit.jsonl`: `13ba12736144cf1f…`

## Sealed Hindi set (`heldout_hindi.jsonl`, committed before its first run; never tuned on)

12 scam + 12 legitimate messages. LLM verdict used for 24 of 24 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 1.00 (12/12) | ≥ 0.85 | yes |
| False alarms on legit | 1 of 12 | ≤ 10% | yes |
| Precision | 0.92 | n/a | |
| Median latency | 1527.31 ms | ≤ 6000 ms | yes |
| p95 / max latency | 4013.99 / 4376.33 ms | n/a | |
| Scam-type accuracy (flagged scams) | 8/12 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| hi | 12 | 12 |

Missed scams:

- none

False alarms:

- `g05` (score 69): आपका अमेज़न पैकेज आज शाम 6 बजे तक डिलीवर होगा। डिलीवरी के समय ओटीपी 4821 डिलीवरी एजेंट को 

## Sealed test set 3 (`heldout3.jsonl`, committed before the LLM calibration)

10 scam + 12 legitimate messages. LLM verdict used for 21 of 22 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 0.90 (9/10) | ≥ 0.85 | yes |
| False alarms on legit | 0 of 12 | ≤ 10% | yes |
| Precision | 1.00 | n/a | |
| Median latency | 1084.52 ms | ≤ 6000 ms | yes |
| p95 / max latency | 2156.68 / 4529.33 ms | n/a | |
| Scam-type accuracy (flagged scams) | 6/9 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 8 | 9 |
| ta | 1 | 1 |

Missed scams:

- `m05` (lottery_prize, en, score 35): Congratulations! Your number won Rs 15 lakh in the Airtel lucky draw. Send Rs 7,800 GST to...

False alarms:

- none

## Sealed test set 2 (`heldout2.jsonl`, never tuned on by the rules)

15 scam + 10 legitimate messages. LLM verdict used for 25 of 25 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 1.00 (15/15) | ≥ 0.85 | yes |
| False alarms on legit | 0 of 10 | ≤ 10% | yes |
| Precision | 1.00 | n/a | |
| Median latency | 930.41 ms | ≤ 6000 ms | yes |
| p95 / max latency | 4011.05 / 4016.32 ms | n/a | |
| Scam-type accuracy (flagged scams) | 14/15 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 10 | 10 |
| hi | 2 | 2 |
| ta | 3 | 3 |

Missed scams:

- none

False alarms:

- none

## Sealed call transcripts (`heldout_calls.jsonl`, committed before the call-scam rules)

10 scam + 6 legitimate messages. LLM verdict used for 15 of 16 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 1.00 (10/10) | ≥ 0.85 | yes |
| False alarms on legit | 1 of 6 | ≤ 10% | **no** |
| Precision | 0.91 | n/a | |
| Median latency | 1250.48 ms | ≤ 6000 ms | yes |
| p95 / max latency | 2258.06 / 2599.71 ms | n/a | |
| Scam-type accuracy (flagged scams) | 8/10 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 8 | 8 |
| hi | 1 | 1 |
| ta | 1 | 1 |

Missed scams:

- none

False alarms:

- `d01` (score 55): hello sir i am the delivery boy from amazon i am near your street can you tell me which bu

History: held-out set 1 scored recall **0.13** (2/15) on its first, honest run with the original keyword rules. That exposed overfitting and a URL bug; the rules were then generalised and the sealed set above was written before those changes.

## Held-out set 1 (`heldout.jsonl`, used for tuning after its first run)

15 scam + 10 legitimate messages. LLM verdict used for 25 of 25 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 1.00 (15/15) | ≥ 0.85 | yes |
| False alarms on legit | 1 of 10 | ≤ 10% | yes |
| Precision | 0.94 | n/a | |
| Median latency | 1341.85 ms | ≤ 6000 ms | yes |
| p95 / max latency | 3157.61 / 4007.70 ms | n/a | |
| Scam-type accuracy (flagged scams) | 12/15 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 10 | 10 |
| hi | 2 | 2 |
| ta | 3 | 3 |

Missed scams:

- none

False alarms:

- `g05` (score 45): Uncle, please transfer the rent to the usual account by Friday. I will send the receipt.

## Development set (`scams.jsonl` + `legit.jsonl`)

40 scam + 20 legitimate messages. LLM verdict used for 60 of 60 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 1.00 (40/40) | ≥ 0.85 | yes |
| False alarms on legit | 0 of 20 | ≤ 10% | yes |
| Precision | 1.00 | n/a | |
| Median latency | 1113.86 ms | ≤ 6000 ms | yes |
| p95 / max latency | 4007.41 / 4018.31 ms | n/a | |
| Scam-type accuracy (flagged scams) | 35/40 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 27 | 27 |
| hi | 3 | 3 |
| ta | 10 | 10 |

Threshold sweep (medium cut-off):

| Medium ≥ | Recall | False alarms |
| --- | --- | --- |
| 25 | 1.00 | 0 |
| 30 | 1.00 | 0 |
| 35 | 1.00 | 0 |
| 40 | 1.00 | 0 |
| 50 | 1.00 | 0 |

Missed scams:

- none

False alarms:

- none

## Caveats

- Results for each message are in `eval/results/<set>.jsonl`.
- Without an LLM key every verdict is `confidence: "lower"`. Re-run with the LLM configured and report both modes.
- The Hindi keyword lists were reviewed by the team's Hindi speaker (no changes needed); the Tamil list was never reviewed, and Tamil is no longer offered to users.
- Small sets: one message changes recall by 2.5 to 7 points. Treat these as indicative.
- One author wrote every set, including the sealed one; messages written by other team members would be a fairer test.
