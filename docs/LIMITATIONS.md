# Known limitations: analysis engine (Person 2)

The guide's definition of done asks for known limitations to be written down. These are measured or observed, not guessed.

## Accuracy
- **Small, team-written test sets.** With the LLM (gpt-oss-120b on Groq): newest sealed set 10/10 scams, 0/12 false alarms; all sets 90/90 scams, 2 of 58 genuine messages at "may be a scam". Rules only (no internet): 13/15 and 0 false alarms on the older sealed set. One author wrote every set, so a larger real-world evaluation is the next step.
- **Remaining LLM false alarms** are medium only, by design (the LLM alone cannot reach high): a delivery call asking for directions, and a family message about paying rent.
- **Reply time measured on a laptop** (median about 1.2 s, p95 about 4 s with the LLM and network checks); not yet on the demo server. Groq's free tier limits requests per minute.
- **Spoken numbers.** Speech-to-text writes "press nine" or "thirty minutes" as words, and the urgency, press-key and OTP patterns only match digits (2 of the 10 sealed calls were missed this way).
- **Without the LLM**, job-offer scams that do not ask for money yet ("reply YES to start") score low; with the LLM they are caught.
- **Tamil and Hindi keyword lists** have not been reviewed by a native speaker.

## OCR and evidence
- **Tesseract reads the ₹ sign as "=", "~" or "7".** The first two are recovered; a leading "7" is ambiguous, so that amount is left for the user to type rather than guessed.
- **Tamil OCR** needs the Tamil language pack installed with Tesseract (`tesseract --list-langs` must show `tam`). Measured on a browser-rendered Tamil screenshot: one character wrong in a 30-word message, verdict HIGH. Blurry phone photos will do worse.

## Link and file checks
- **WHOIS, Safe Browsing and VirusTotal** are skipped without keys or internet; the offline lookalike, suspicious-TLD and local URLhaus checks still run.
- **The URLhaus list is a snapshot.** Refresh it with `python -m kavach.analysis.blocklist --update` before the demo. PhishTank is not included because it now requires a registered application key.
- **The APK scanner is static.** It reads the manifest only; heavily obfuscated or packed APKs can fail to parse, and are then reported as "could not read this file, do not install it".
- **Uploads are capped at 20 MB** (guide section 11).

## Scam Pulse
- **Runs on seeded demo data** until real users report; the clustering code is real.
- **District is not collected yet** by the WhatsApp flow, so live reports are not stored until Person 1 adds it (`docs/person1_integration.patch`).
- **With the default TF-IDF embeddings**, the English and Tamil copies of one scam wave show as two alerts. The optional e5 model joins them, but its margin on the seed data is thin.

## Integration
- **Person 1's flow does not yet call** the Bait Verifier or the receipt OCR; the ready patch is `docs/person1_integration.patch`.
- **Voice notes** need speech-to-text (Person 1's language service) before they can be checked; without it the verdict is `UNKNOWN`, never "safe".
