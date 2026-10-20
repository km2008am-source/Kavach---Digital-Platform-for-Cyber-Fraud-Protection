# Member 3 handoff

## Run
- Backend: `cd backend && pip install -r requirements.txt && DEMO_MODE=1 uvicorn kavach.main:app --port 8000`
- Web (dev): `cd web && npm install && npm run dev` (proxies /api to :8000). Production: `npm run build`; FastAPI serves `web/dist`.
- Tests: `cd backend && python -m pytest -q` and `cd web && npx vitest run`.

## Stand-ins to delete when the real code lands (same import paths)
- M1: `main.py`, `config.py`, `db.py` (merge `SimSession`, `NewsItem`), `whatsapp/client.py` (DRY_RUN outbox), `language/service.py` (translate pass-through). M1 must also mount `/api/services`.
- M2: `analysis/scam_check.py`, `pulse.py`, `news_tagger.py`, `llm.py`.

## Additions that need team sign-off (section 5 says names are frozen)
- New endpoint `POST /api/sim/quiz` (before/after quiz). New env vars: `DEMO_USER_LANG`, `CALL_SPEECH_LANG`, `NEWS_FEEDS`, `WEB_ORIGINS`. New `sim_session.post_score` column.
- `POST /api/pulse/replay` returns 403 unless `DEMO_MODE=1` (section 11).

## Still to do by hand (cannot be done in code)
1. Record `backend/kavach/static/screening_notice.mp3` (Tamil then English). Until then the call says the notice in English with Twilio's voice.
2. Have a Tamil speaker review the keyword lists in `simulator/scoring.py` and the Tamil strings in the scenario file.
3. Confirm on Twilio whether `ta-IN` speech is offered; set `CALL_SPEECH_LANG` accordingly.
4. Fill `official_numbers.json` for more organisations from their official sites only (SBI is filled and was checked against sbi.bank.in on 2026-10-20).
5. Slide 2: confirm the 1,935 crore figure against the primary Parliament reply.
6. Choose and test RSS feeds from the venue network, then set `NEWS_FEEDS`; otherwise the hand-picked demo news is shown and labelled.
7. Record the backup video (H32) and export the deck to PDF.

## Browser smoke test
`cd web && npm run build`, start the backend (`DEMO_MODE=1`), then `python tests_e2e/smoke.py` (needs `pip install playwright`). It walks Analyze, Services, News, a full Simulator session and the Pulse replay. One console error is expected until M1 mounts `/api/services` (the page then shows labelled demo data).

## Known limitations (say them honestly if asked)
- The fallback judge in `simulator/scoring.py` is keyword-based: it handles simple negation ("don't hang up") but not sarcasm or long sentences. With a working LLM it only caps a "complying" reply; with the LLM down it decides alone.
- With the LLM down, the call repeats the final "payment" line for turns 5 to 8.
- The in-memory rate limits (30 checks and 60 simulator calls per minute per IP) are shared by everyone behind the same venue Wi-Fi address; raise them in `api/analyze.py` and `api/sim.py` if many judges try the site at once.
- No request-size cap at the app level except 20 MB uploads and per-field limits; put a body limit on Caddy.
- Sessions, rate limits and Twilio call IDs live in process memory: a restart mid-demo loses an in-progress simulation (the page offers "Start over") but nothing else.
- Twilio's own console shows recognised speech for trial calls. Kavach stores no audio and logs no transcripts.
