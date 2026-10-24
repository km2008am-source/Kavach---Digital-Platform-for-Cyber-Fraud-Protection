# Member 2 demo run-sheet

Guide section 14 gives Member 2 three demo duties:

1. Play the fake customs officer on the Call Shield call (step 1).
2. Run the Pulse replay if needed (step 6).
3. Own the `DEMO_MODE` backup.

Everything below has been tested offline.

## 30 minutes before

Run these from `backend/` on the demo server (or Person 1's laptop):

```bash
git pull
python -m kavach.analysis.blocklist --update           # fresh URLhaus list (works offline afterwards)
python ../eval/evaluate.py --write-demo-cache          # refresh cached verdicts for the demo inputs
python -m kavach.analysis.cli --pulse-replay           # seed Scam Pulse; expect Coimbatore alert(s)
python -m kavach.analysis.cli "sir this is customs, your parcel has drugs, press 1"   # expect MEDIUM/HIGH
```

Check `backend/.env` on the demo server:

| Variable | Demo value | Why |
| --- | --- | --- |
| `APP_ENV` | `demo` | Refuses to start with a weak `HASH_SALT` |
| `HASH_SALT` | a random 64-character value | Protects Pulse reporter IDs |
| `DEMO_MODE` | `0`; switch to `1` only if the venue internet or LLM fails | Cached answers for the prepared inputs |
| `PULSE_EMBEDDINGS` | `e5` if the model is downloaded, otherwise `tfidf` | With e5 the Coimbatore wave is **one** alert (English + Tamil); with TF-IDF it shows as two |

## Prepared inputs (keep them exactly as written)

They're stored in `data/samples/demo_inputs.jsonl`. `DEMO_MODE` only recognises them **word for word**, so copy them from that file onto the demo phone instead of retyping.

| Demo step | What | Offline verdict |
| --- | --- | --- |
| 2 | KYC SMS with the `sbi-kyc-update.xyz` link | HIGH (85), "Fake look-alike website" |
| Bait | "verify PM Free Laptop Yojana 2026 …" | HIGH (90), points to PIB Fact Check |
| 3 | `data/samples/apks/rto_challan_test.apk` | HIGH (90), "Do not install" |
| 4 | `data/samples/receipts/r01.png` and `r02.png` | Transaction ID and amount read by OCR |
| Hindi | On the website's Check a message page, press **हिंदी उदाहरण**, then **Check it** | HIGH; the whole result card in Hindi |
| Hindi screenshot | A screenshot of the same Hindi SMS | Same verdict as the text; read by Tesseract, or by the vision model if Tesseract is missing |

Screenshots need one of these on the demo machine: Tesseract with the Hindi pack, or
`OCR_VISION_MODEL=qwen/qwen3.8-27b` in `backend/.env`. Check which one is active:
`python -c "from kavach.analysis import ocr; print(ocr.engine())"` prints `tesseract`, `vision` or `none`.

## Step 1: the customs-officer call (Member 2 speaks)

Call the Kavach Twilio number when Member 3 cues you. After the notice, speak slowly and clearly. Any one of these lines is caught **even with no internet and no LLM**:

- "Sir, this is customs. Your parcel has drugs. Press 1." (MEDIUM, 60)
- "Hello, I am calling from customs. Your courier parcel has been stopped, there are illegal items inside. You must speak to the officer now." (MEDIUM, 65)
- "Your parcel has illegal items. Pay a fine or face arrest." (HIGH, 80)

**Say words, not numbers, carefully:** speech-to-text may write "press one" as "press one", and digit-only rules miss that (a known gap, see `eval/report.md`). The words "customs", "parcel", "drugs" / "illegal items" and "officer" carry the verdict on their own.

Then hang up. Lakshmi's phone should show the alert. (The Twilio → `analyze()` link is Member 3's Call Shield.)

## Step 6: Scam Pulse

If the map is empty, run:

```bash
python -m kavach.analysis.cli --pulse-replay
```

Pressing it twice is safe: the replay replaces its own seed rows. Say: *"This is demo data from our seeded replay; the clustering code is real."*

## If something fails

| Failure | What to do |
| --- | --- |
| LLM down or slow | Nothing: rules + links still give verdicts (`confidence: lower`) |
| Venue internet down | Set `NETWORK_CHECKS=0` and `DEMO_MODE=1`, restart; the prepared inputs answer instantly |
| A judge asks "try this message" | `python -m kavach.analysis.cli "<their text>"` on the laptop shows the verdict and every red flag |
| Pulse map empty | Run the replay command above |
