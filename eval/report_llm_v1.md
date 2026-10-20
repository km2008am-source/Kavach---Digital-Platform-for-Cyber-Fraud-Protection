# Kavach Scam Check: evaluation report

Generated 2026-10-20 20:39 by `eval/evaluate.py`. Owner: Member 2. All phone numbers, UPI IDs and links in the datasets are fake.

**Quote the sealed-set numbers on the slide.** It was written before the last rule changes and was never used for tuning. The other two sets were used to write the rules, so their numbers are optimistic.

## Run configuration

| Component | State for this run |
| --- | --- |
| Code version | git `746de7f` + uncommitted changes |
| LLM classifier | **on** (`openai/gpt-oss-120b` at `api.groq.com`) |
| Network reputation checks (`NETWORK_CHECKS`) | **on** |
| Google Safe Browsing | off |
| VirusTotal URL lookup | off |
| WHOIS domain age | **on** |
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

15 scam + 10 legitimate messages. LLM verdict used for 25 of 25 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 1.00 (15/15) | ≥ 0.85 | yes |
| False alarms on legit | 2 of 10 | ≤ 10% | **no** |
| Precision | 0.88 | n/a | |
| Median latency | 1023.24 ms | ≤ 6000 ms | yes |
| p95 / max latency | 2574.56 / 2686.03 ms | n/a | |
| Scam-type accuracy (flagged scams) | 14/15 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 10 | 10 |
| hi | 2 | 2 |
| ta | 3 | 3 |

Missed scams:

- none

False alarms:

- `q01` (score 70): Your Axis Bank debit card ending 4421 was used for Rs 640 at Big Bazaar. If not done by yo
- `q03` (score 40): Your PM Kisan installment of Rs 2,000 has been credited to your bank account. - PM Kisan

## Sealed call transcripts (`heldout_calls.jsonl`, committed before the call-scam rules)

10 scam + 6 legitimate messages. LLM verdict used for 16 of 16 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 1.00 (10/10) | ≥ 0.85 | yes |
| False alarms on legit | 4 of 6 | ≤ 10% | **no** |
| Precision | 0.71 | n/a | |
| Median latency | 1133.85 ms | ≤ 6000 ms | yes |
| p95 / max latency | 1501.53 / 1716.93 ms | n/a | |
| Scam-type accuracy (flagged scams) | 7/10 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 8 | 8 |
| hi | 1 | 1 |
| ta | 1 | 1 |

Missed scams:

- none

False alarms:

- `d01` (score 70): hello sir i am the delivery boy from amazon i am near your street can you tell me which bu
- `d03` (score 72): hi ma'am i am calling from your bank branch your new cheque book is ready you can collect 
- `d05` (score 80): sir this is from the passport office the police verification officer will visit your house
- `d06` (score 70): வணக்கம் நான் கேஸ் ஏஜென்சியிலிருந்து பேசுகிறேன் உங்கள் சிலிண்டர் நாளை காலை டெலிவரி செய்யப்ப

History: held-out set 1 scored recall **0.13** (2/15) on its first, honest run with the original keyword rules. That exposed overfitting and a URL bug; the rules were then generalised and the sealed set above was written before those changes.

## Held-out set 1 (`heldout.jsonl`, used for tuning after its first run)

15 scam + 10 legitimate messages. LLM verdict used for 25 of 25 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 1.00 (15/15) | ≥ 0.85 | yes |
| False alarms on legit | 1 of 10 | ≤ 10% | yes |
| Precision | 0.94 | n/a | |
| Median latency | 1193.74 ms | ≤ 6000 ms | yes |
| p95 / max latency | 2214.90 / 2450.98 ms | n/a | |
| Scam-type accuracy (flagged scams) | 13/15 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 10 | 10 |
| hi | 2 | 2 |
| ta | 3 | 3 |

Missed scams:

- none

False alarms:

- `g10` (score 78): Police Verification for your passport is scheduled. The officer will visit your address be

## Development set (`scams.jsonl` + `legit.jsonl`)

40 scam + 20 legitimate messages. LLM verdict used for 56 of 60 messages.

| Metric | Value | Target (guide) | Met? |
| --- | --- | --- | --- |
| Recall on scams | 0.97 (39/40) | ≥ 0.85 | yes |
| False alarms on legit | 2 of 20 | ≤ 10% | yes |
| Precision | 0.95 | n/a | |
| Median latency | 1114.81 ms | ≤ 6000 ms | yes |
| p95 / max latency | 4009.13 / 4015.79 ms | n/a | |
| Scam-type accuracy (flagged scams) | 37/39 | n/a | |

| Language | Scams flagged | Total |
| --- | --- | --- |
| en | 27 | 27 |
| hi | 3 | 3 |
| ta | 9 | 10 |

Threshold sweep (medium cut-off):

| Medium ≥ | Recall | False alarms |
| --- | --- | --- |
| 25 | 1.00 | 2 |
| 30 | 1.00 | 2 |
| 35 | 1.00 | 2 |
| 40 | 0.97 | 2 |
| 50 | 0.95 | 1 |

Missed scams:

- `s29` (investment, ta, score 35): பங்குச் சந்தையில் ஒரு மாதத்தில் இரட்டிப்பு லாபம் உறுதி. எங்கள் வாட்ஸ்அப் குழுவில் சேர்ந்து...

False alarms:

- `l02` (score 78): Rs 2,450.00 debited from A/c XX1234 on 12-10-26 to Swiggy. Avl Bal Rs 18,320.50. Not you? 
- `l18` (score 40): Your LIC premium of Rs 4,500 is due on 30 October. Pay through the LIC app or at any LIC b

## Caveats

- Results for each message are in `eval/results/<set>.jsonl`.
- Without an LLM key every verdict is `confidence: "lower"`. Re-run with the LLM configured and report both modes.
- Tamil and Hindi keyword lists need review by a native speaker.
- Small sets: one message changes recall by 2.5 to 7 points. Treat these as indicative.
- One author wrote every set, including the sealed one; messages written by other team members would be a fairer test.
