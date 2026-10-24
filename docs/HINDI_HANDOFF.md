# Hindi support: what is done and what each member still needs to change

The team chose Hindi instead of Tamil (one Hindi speaker on the team can review every line).
Tamil is removed from the website and stays on the roadmap. The analysis engine still
recognises Tamil scam words, so a Tamil scam is still caught; Tamil is simply not offered.

## Done (Member 2, branch `hindi-support`)

| Where | What |
| --- | --- |
| `backend/kavach/analysis/rules.py` | Hindi (Devanagari) and Hinglish scam phrases for every red flag and scam type, in one `_HINDI` block for review. "गिरफ़्तार" and "गिरफ्तार" match the same way. Hindi rupee amounts ("5000 रुपये") are extracted. |
| `backend/kavach/analysis/bait.py` | Hindi asks (पंजीकरण, आधार, शेयर करें...) and Hindi warnings ("ओटीपी किसी को न बताएं") counted as advice, not as an ask. |
| `backend/kavach/analysis/ocr.py` | Reads screenshots with Tesseract (Hindi needs the `hin` pack) or, when Tesseract is missing, with the vision model in `OCR_VISION_MODEL` (Hindi read exactly in tests). |
| `backend/kavach/analysis/scam_check.py` | When the user picks Hindi, the LLM writes its reasons and explanation in Hindi. |
| `backend/tests/test_hindi.py` | 9 Hindi/Hinglish scams flagged and 8 genuine Hindi messages (including two bank OTP warnings) not flagged, all with the LLM off. |
| `web/` | Hindi in the masthead and Home page; Check a message offers English / हिंदी and shows the result card (risk, scam type, reasons, what to do, buttons) in Hindi; a "हिंदी उदाहरण" sample button; Training shows Hindi as "coming soon"; Devanagari font. All Tamil removed from the site. |

**Sealed Hindi set** (`data/samples/heldout_hindi.jsonl`, 12 scams + 12 genuine, committed before its first run,
never tuned on), with the LLM: **12 of 12 scams caught, 1 false alarm in 12 genuine messages**. The false alarm is
a genuine Amazon delivery message that tells you to give the OTP to the delivery agent (scored medium).

Measured with the LLM off: 0 of 8 genuine Hindi messages flagged; 9 of 10 Hindi scams flagged
(the 10th, an electricity-cut message, scores 35 of the 40 needed; the English version behaves
the same and relies on the LLM). English results on every evaluation set are unchanged.

## Member 1 (backend owner): about 10 minutes

1. `backend/kavach/language/service.py`, so WhatsApp replies and translations work in Hindi:
   ```python
   SUPPORTED_LANGUAGES = {"en", "hi"}          # Tamil removed from what users get

   # in detect_language(), after the empty check:
   if any("ऀ" <= char <= "ॿ" for char in cleaned):   # Devanagari block
       return "hi"
   ```
   The Tamil branch in `detect_language` can be deleted.
2. `backend/kavach/flows/intents.py`: add Hindi "I lost money" phrases next to the Tamil ones:
   `"पैसे चले गए"`, `"पैसे कट गए"`, `"ठगी हो गई"`, `"paise kat gaye"`, `"fraud ho gaya"`; and `"नमस्ते"` to `MENU_WORDS`.
3. Optional: when merging Member 3's `/api/analyze` into `backend/`, translate the explanation for Hindi.
   The LLM already writes it in Hindi; this only matters when the LLM is down and the rules write it in English:
   ```python
   result = await asyncio.wait_for(analyze(req), TIMEOUT)
   if body.language == "hi" and result.explanation_en:
       try:
           result.explanation_en = await translate(result.explanation_en, source="en", target="hi")
       except Exception:
           pass                      # keep English rather than fail the check
   return result
   ```
4. Deployment, either one: install Tesseract with the Hindi pack (`apt install tesseract-ocr tesseract-ocr-hin`),
   or set `OCR_VISION_MODEL=qwen/qwen3.8-27b` in `backend/.env` so the Groq vision model reads screenshots.

## Member 3 (Training simulator and calls): after the backend merge

1. `api/sim.py`: `language: Literal["en", "hi"] = "en"`.
2. `simulator/engine.py`: `LANG_NAME = {"en": "English", "hi": "Hindi"}`; add `"hi"` to `CLOSING`
   and the "stopped" text; the quiz key for Hindi (`q_hi`).
3. `simulator/scenarios/digital_arrest.json`: a `"hi"` line next to each `"en"` line, and `q_hi` quiz questions.
4. `simulator/scoring.py`: Hindi resist / comply keywords (for example "नहीं दूँगा", "कॉल काट रहा हूँ",
   "बैंक से पूछूँगा", "पुलिस को बताऊँगा" for resisting; "ठीक है भेज रहा हूँ", "ओटीपी है" for complying)
   and a `"hi"` block in `_T`.
5. Calls: set `CALL_SPEECH_LANG=hi-IN` and use a Hindi voice for the notice; test one real call.
6. Website: in `web/src/pages/Simulator.jsx`, replace the disabled Hindi radio with an enabled one:
   ```jsx
   <label lang="hi"><input type="radio" name="sl" value="hi" checked={language === 'hi'} onChange={() => setLanguage('hi')} />हिंदी</label>
   ```
   Speech input and output already switch to `hi-IN`.

Vani (Hindi speaker) reviews every Hindi line from steps 3 and 4 before the demo.

## Slides and pitch

- Say: "Kavach checks messages in English, Hindi and Hinglish, and explains the result in Hindi."
- Training in Hindi: say "coming next" until Member 3's steps are done.
- Tamil: roadmap slide only.
