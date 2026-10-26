# Kavach

**A Telegram bot and web app that help protect people before, during, and after a scam, in Hindi or English.**

Kavach is a hackathon prototype for digital fraud protection in India. It checks suspicious messages, links, screenshots, and APK files; screens suspicious phone calls through Twilio Call Shield; and guides people who have lost money toward urgent next steps. Its current bot demo uses Telegram, with English and Hindi language support.

> Built as a 3-person hackathon prototype. Features that use seeded or demo data are labelled as such in this README and in the demo.

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Introduction](#2-introduction)
3. [What the Project Does](#3-what-the-project-does)
4. [How Kavach Differs from Current Solutions](#4-how-kavach-differs-from-current-solutions)
5. [Methodology](#5-methodology)
6. [Conclusion](#6-conclusion)
7. [Getting Started](#7-getting-started)
8. [Limitations and Honest Notes](#8-limitations-and-honest-notes)
9. [Team](#9-team)

---

## 1. Problem Statement

Indian citizens lose money to scams that rely on **real-time pressure**: fake police or customs calls (“digital arrest”), KYC-expiry threats, malicious APK files sent through messaging apps, fake UPI collect requests, courier-customs scams, and fake investment or job offers.

Three failures make these scams so effective:

| Failure point | What happens |
| --- | --- |
| **Pressure in the moment** | The victim is kept on the phone, told not to tell anyone, and pushed to pay or share an OTP before they can think or verify. |
| **Late response after the fraud** | Recovery chances are highest when the victim reports quickly, but people often don't know whom to call, panic, or delay. They may reach the helpline without the transaction details the operator needs. |
| **Scattered, hard-to-reach help** | Government channels exist (the **1930** helpline, **cybercrime.gov.in**, **Sanchar Saathi**, **RBI Sachet**), but they are spread across different sites and are not always easy to find in a stressful moment. |

People with less experience using digital services can be especially vulnerable to pressure and confusing reporting steps.

**Target user:** smartphone users in India, with a focus on people who need clear, accessible guidance. The demo persona is **Lakshmi, 62, from Lucknow**, who speaks Hindi and receives a call from a “customs officer”.

---

## 2. Introduction

**Kavach** (Hindi/Sanskrit for “armour”) brings scam checking, response guidance, and training together in a Telegram bot and a web app. Users can send suspicious text, a link, a screenshot, an APK, or a voice note to the configured Telegram bot and receive a plain-language safety check in English or Hindi. The web app provides a browser-based way to use several project features.

Kavach is organised around the full lifecycle of a scam:

| Stage | What Kavach does | Features |
| --- | --- | --- |
| **Before** | Helps people recognise scams and builds resistance | Manipulation X-Ray Simulator, Scam Pulse, Scam News Feed, Private DNS guide |
| **During** | Acts at the moment of attack | Call Shield, Scam Check + Link Scanner, APK Scanner, Scam Bait Verifier, Family Guardian alert |
| **After** | Gets victims to the right authority, fast | Golden Hour Responder, Report Router, Government Services Hub |

Every verdict **explains its reasoning in plain words**, so users can learn to spot red flags rather than relying on a black box.

---

## 3. What the Project Does

### Core features (P0)

**Scam Check + Link Scanner**  
Analyses text, URLs, screenshots via OCR, and call transcripts. It returns a risk level (low / medium / high), a scam type, explanatory red flags, and a recommended action. Links can be checked against blocklists, lookalike-domain detection, and domain-age information when those checks are available.

**APK Scanner**  
Statically inspects APK files **without running them**. It can check the SHA-256 hash, requested permissions, and combinations of permissions that may indicate risk. It can flag apps that claim to be official while requesting sensitive access. This is a prototype check and does not guarantee that an APK is safe.

**Golden Hour Responder + Report Router**  
For users who say they have already paid, Kavach tells them to **call 1930 first**, collects transaction details and screenshots, attempts to extract receipt details, provides bank-specific guidance where available, and creates a complaint draft and **PDF evidence pack**. Users can add their 1930 acknowledgement number. The guidance points users to official reporting channels; Kavach does not file complaints for them.

**Call Shield**  
Uses Twilio Voice to screen a call by asking the caller for their name and reason. The caller's response can be transcribed and analysed, and the configured user can receive an alert through the bot. Production use would require proper call-forwarding setup; the hackathon demo uses a configured Twilio number.

**Manipulation X-Ray Simulator**  
A training simulation of a “digital arrest” call. An LLM plays a **fictional** officer from a **fictional** agency, while the interface labels pressure tactics such as urgency, authority, isolation, fear, secrecy, and payment pressure. The user receives a debrief and a resilience score.

**Language support (Hindi + English)**  
The current messaging flow supports English and Hindi text. Optional voice support can transcribe voice notes and generate spoken replies when the voice dependencies are installed.

### Recommended features (P1)

| Feature | Description |
| --- | --- |
| Scam Pulse | Uses opt-in, anonymised reports and a user-selected district to identify possible scam waves. The demo replay and displayed examples can use seeded data. |
| Government Services Hub | Situation-based cards (“I lost money”, “I lost my phone”, “Someone is using my ID”) that link to official services |
| Scam Bait Verifier | Checks forwarded fake-news and fake-scheme posts using the “Follow the Ask” test and points users to PIB Fact Check and myScheme.gov.in |
| Family Guardian alert | High-risk alerts are available through the messaging flow when the recipient is configured for the active messaging provider. Telegram requires a Telegram chat ID. |
| Private DNS guide | Step-by-step guide to enable filtered DNS on a phone |
| Scam News Feed | Shows scam news. Hand-picked articles are labelled as demo content until RSS feeds are configured. |

### Channels

- **Telegram bot:** the current messaging demo for text, links, screenshots, APKs, and voice notes
- **Phone line (Twilio Voice):** Call Shield
- **Web app (React):** Analyze page, Simulator, Pulse, Services Hub, and News

---

## 4. How Kavach Differs from Current Solutions

| Existing approach | What it does | Gap | How Kavach is different |
| --- | --- | --- | --- |
| **Caller-ID apps** (Truecaller-style) | Labels a number as spam based on community reports | Only labels numbers; can't judge what the caller says; new scam numbers may not be labelled yet | Call Shield **asks the caller for a reason**, analyses what they say, checks the claimed organisation against its official numbers, and can treat a hang-up as a signal |
| **Government portals** (1930, cybercrime.gov.in, Sanchar Saathi, RBI Sachet) | Official reporting and recovery channels | A panicked user may not know which channel to use or what transaction details to prepare | Kavach **routes users to these channels** (1930 is the first instruction after money loss) and helps prepare evidence. It doesn't replace the authorities |
| **Antivirus / security apps** | Scan installed apps and files | Require installation and may not help with suspicious messages, calls, or post-fraud steps | Kavach can check supported messages, links, screenshots, and APK files through its bot or web app, with plain-language explanations |
| **Awareness campaigns and websites** | Educate through posters, videos, and articles | Passive; don't act at the moment of attack; rarely personalised or interactive | The X-Ray Simulator lets users **experience** pressure tactics safely and review their responses |
| **Bank SMS / app alerts** | Warn users about fraud in general | Generic and limited to a particular bank | Kavach can assess supported content from different sources and explain the warning signs |
| **Generic AI chatbots** | Can answer questions about scams | Not designed for call screening, evidence packs, official routing, or scam-wave detection; a model alone can be misled | Kavach combines rules, link checks, and an LLM so the LLM is **not the only safeguard**, and rule-based checks can still run when the LLM is unavailable |

**What makes Kavach competitive**

- It helps during an attack through Call Shield and after a loss through the Golden Hour Responder.
- A Telegram bot and web app provide ways to access the prototype.
- **Explainable** verdicts and a simulator score help users understand the advice.
- **Privacy-conscious reporting:** Scam Pulse is opt-in, uses a user-selected district, and normalises report text before storage.

---

## 5. Methodology

### 5.1 Approach

Kavach is built as one **FastAPI modular monolith** with three entry points (Telegram, phone, web) and shared analysis code. A single process is enough for a hackathon prototype and avoids network calls between the team members' modules. The work is split by layer so the team can develop against shared data contracts.

### 5.2 System architecture

```text
  Telegram user          Phone caller              Browser user
       |                      |                          |
 Telegram Bot API        Twilio Voice              React web app
       |                      |                          |
 POST /webhook/telegram  POST /twilio/voice|gather   /api/*  (REST)
       \______________________|__________________________/
                              |
                     FastAPI app (kavach/)
   +--------------+-----------+------------+--------------+
   | messaging/   | calls/    | simulator/ | api/ (web)   |   <- entry modules
   | flows        |           |            |              |
   +------+-------+-----+-----+------+-----+------+-------+
          |             |            |            |
   +------v-------------v------------v------------v-------+
   | analysis/: scam_check, links, ocr, apk, bait,        |
   |            evidence, pulse, news_tagger              |
   | language/: detect, translate, stt, tts               |
   | llm.py: one JSON-returning LLM wrapper               |
   +------+------------------------------+----------------+
          |                              |
     SQLite (kavach.db)          External services: Safe Browsing,
     + files/ (temporary)        VirusTotal, WHOIS, LLM, Telegram,
                                 Twilio
```

The messaging modules currently live under `backend/kavach/whatsapp/` in the codebase. That directory name is retained in the repository; the active bot demo uses Telegram.

### 5.3 How a Telegram check flows

1. Telegram sends an update to the public webhook; the app checks the webhook secret, acknowledges promptly, and de-duplicates message IDs.
2. A background task downloads any media, transcribes voice notes when voice support is installed, and builds an `AnalysisRequest`.
3. The analysis module returns an `AnalysisResult`.
4. The flow layer formats and translates the reply, then sends it to the Telegram chat.
5. If the user opted in with a district, eligible medium- or high-risk text checks may be added to Scam Pulse in anonymised form.

Each bot user has a conversation state (`IDLE`, or `GH_*` for Golden Hour steps). The word `menu` always resets the state, so users can leave a flow.

### 5.4 The verdict engine (three independent signals)

```text
Input -> OCR (if image) -> entity extraction -> rule flags -> link checks -> LLM classification -> score fusion
```

| Signal | What it does | Why it matters |
| --- | --- | --- |
| **Rule engine** | Detects phones, UPI IDs, URLs, and amounts; applies weighted indicators such as credential requests, arrest threats, urgency, payment requests, KYC pressure, and isolation in supported languages | Fast, explainable, and works without an LLM |
| **Link intelligence** | Uses configured reputation checks, lookalike-domain detection, and domain-age information | Can identify suspicious links that a simple keyword check misses |
| **LLM classifier** | Returns a scam type, risk score, red flags, and an explanation as validated JSON | Adds context for messages that rules alone may not understand |

**Score fusion:** the strongest signal contributes to the verdict, and agreement between independent signals can increase the score. Risk levels use configured thresholds. The result is an estimate, not proof that content is safe or malicious.

**Safety properties**

- **Prompt-injection defence:** user content is passed to the LLM as data, while rules and link checks run independently.
- **Graceful degradation:** if the LLM is unavailable, the verdict can fall back to rules and available link checks.
- **Source failures never block a verdict:** if an optional reputation source fails, the other available checks can still be used.

### 5.5 Language layer

The current bot flow supports English and Hindi. Optional voice support uses faster-whisper for speech-to-text and gTTS for spoken replies; translation uses `deep-translator`. Voice features require the optional voice dependencies and may need an internet connection.

### 5.6 Scam Pulse (scam-wave detection)

Users can opt in by sending `district <name>` and opt out with `district off`. Kavach uses the district the user supplied; it does not collect GPS for this feature. Eligible reports are normalised before storage, and reporter identifiers are salted and hashed. Scam Pulse uses TF-IDF by default; multilingual E5 embeddings can be enabled as an optional dependency. Alerts require enough reports and distinct reporters to form a cluster. The demo replay may show seeded examples.

### 5.7 Technology stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.11+, FastAPI, Pydantic, SQLite |
| Channels | Telegram Bot API, Twilio Programmable Voice; Meta WhatsApp adapter code remains in the repository |
| AI | OpenAI-compatible LLM API, OCR, scikit-learn; sentence-transformers is optional for Scam Pulse |
| Threat intel | Google Safe Browsing, VirusTotal, python-whois, rapidfuzz, androguard (APK analysis) |
| Language | Hindi/English detection, translation, optional faster-whisper and gTTS voice support |
| Documents | ReportLab (PDF evidence pack) |
| Web | React + Vite, Leaflet, Web Speech API |
| Deployment | Linux VM, Nginx, systemd, and public HTTPS |

The prototype uses SQLite and FastAPI background tasks to keep deployment simple. Production use would need operational monitoring, data-retention review, and scalable storage and task processing.

### 5.8 Privacy and security by design

- Uploaded files are stored in the configured files directory and cleaned up by the backend's retention process.
- Scam Pulse stores normalised report text and a salted hash of the reporter identifier; district is supplied by the user, not GPS.
- APKs are **never executed**; VirusTotal lookups use a hash rather than uploading the APK.
- Telegram webhook requests are checked using the configured secret token. Twilio webhooks are validated with `X-Twilio-Signature`.
- The simulator uses a **fictional** agency and persona and is intended for safe training.
- **Failure rule:** a user who may have lost money is directed to call **1930**, even if another feature fails.

### 5.9 Development process

| Aspect | Approach |
| --- | --- |
| Team split | By layer: **Member 1** backend messaging and incident-response flows; **Member 2** AI and threat analysis; **Member 3** voice, web, and pitch |
| Contracts | `backend/kavach/contracts.py` holds the shared Pydantic models used between backend modules |
| Scope | Core and recommended features were prioritised for the hackathon prototype; remaining integrations and production hardening are future work |
| Integration | Features are integrated through the shared FastAPI backend and its Telegram, phone, and web entry points |
| Git | `main` is the shared integration branch; feature branches and pull requests are used for changes |
| Testing | pytest unit and API tests, web checks, and accuracy evaluation on the labelled sample data |

### 5.10 Evaluation plan

| Metric | Target |
| --- | --- |
| Recall on the labelled scam-message set | ≥ 0.85 |
| False alarms on legitimate messages | ≤ 2 in the selected sample |
| Median verdict latency | ≤ 6 s |
| Telegram reply time | Target depends on input type and optional provider availability |
| Evidence extraction on sample receipts | At least 8 of 10 correct |
| Simulator | Resisting sessions should score higher than complying sessions |

Final measured numbers should be taken from `eval/report.md`; targets are not measured results.

### 5.11 Repository layout

```text
kavach/
  backend/kavach/
    main.py  config.py  contracts.py  db.py  llm.py
    whatsapp/    # messaging adapters, webhooks, and media handling
    flows/       # intents, engine, golden_hour, messages
    language/    # detect, translate, stt, tts
    responder/   # router_rules, banks.json, pdf
    analysis/    # scam_check, rules, links, ocr, evidence, apk, bait, pulse, news_tagger
    calls/       # twilio_routes, screening, official_numbers.json
    simulator/   # engine, scoring, scenarios/
    api/         # services, analyze, sim, pulse, news
  web/           # React + Vite app
  data/samples/  # labelled scam / legit dataset, pulse seed
  eval/          # evaluate.py, report.md
  pitch/         # deck, demo script, backup video
  .env.example
```

---

## 6. Conclusion

Scams in India succeed because victims face pressure alone and may lose valuable time before getting help. Kavach addresses several points in that lifecycle: it checks suspicious content, explains risk signals in plain Hindi or English, helps users prepare evidence after a loss, and provides training through the simulator.

The prototype combines rule-based detection, link intelligence, and an LLM while keeping official reporting channels central. Kavach is a support and routing layer; it does not replace banks, police, or government services.

**Roadmap:** improve Telegram deployment and monitoring, complete trusted-contact setup for Telegram, expand language support, gather enough opt-in Scam Pulse reports for meaningful live alerts, and explore an Android share flow and partnerships with banks or telecom operators.

> *Lakshmi recognised the pressure tactics and knew to call 1930.*

---

## 7. Getting Started

### Prerequisites

- Python 3.11 or newer and Node.js with npm
- Git
- A Telegram bot token from BotFather
- A public HTTPS URL for the Telegram webhook (a tunnel such as ngrok can be used during development)
- Optional provider keys for LLM and reputation checks; Twilio credentials are needed for Call Shield

### Setup

## Run locally

Use Python 3.11 or newer and Node.js with npm.

### 1. Start the backend

From the repository root, create and activate a virtual environment, install the backend, and create your local environment file.

**Windows PowerShell:**

~~~powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
Copy-Item .env.example .env
~~~

**Linux or macOS:**

~~~bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
cp .env.example .env
~~~

For the Telegram bot, configure the public webhook URL as:

```text
https://your-public-host/webhook/telegram
```

The bot token and webhook secret in the Telegram webhook setup must match the values in `backend/.env`. Production deployment steps are in `backend/docs/deploy.md`.

### Useful settings

| Variable | Purpose |
| --- | --- |
| `WHATSAPP_PROVIDER=telegram` | Selects the Telegram bot adapter; the setting keeps its existing name in the codebase |
| `TELEGRAM_BOT_TOKEN` | Authenticates the bot with Telegram |
| `TELEGRAM_WEBHOOK_SECRET` | Validates incoming Telegram webhook requests |
| `DRY_RUN=1` | Logs outgoing bot messages instead of sending them |
| `DEMO_MODE=1` | Enables cached verdicts for prepared sample inputs and the Scam Pulse demo replay |
| `PUBLIC_BASE_URL` | Public HTTPS URL used by Twilio Call Shield |

### Connecting channels

- **Telegram:** set the webhook to `PUBLIC_BASE_URL/webhook/telegram` and use the same secret configured in `.env`.
- **Twilio:** set the number's voice webhook to `PUBLIC_BASE_URL/twilio/voice` and configure the Twilio credentials required by Call Shield.

### Running tests

```powershell
cd backend
python -m pip install -e ".[test]"
python -m pytest -q
python ../eval/evaluate.py
```

---

## 8. Limitations and Honest Notes

- **Telegram bot:** requires a public HTTPS webhook for incoming updates. Local testing requires the backend and its HTTPS tunnel to stay running.
- **Twilio trial:** may play a Twilio notice and can call only verified numbers. In production, Call Shield would use conditional call forwarding; the demo calls a configured number directly.
- **Scam Pulse:** the demo replay uses **seeded data**. Live reporting depends on opt-in users, enough reports, and the configured database.
- **Small evaluation set:** results from the team-built sample set do not represent performance on all real-world scams.
- **Hindi OCR and speech accuracy vary** with image and audio quality; user-facing translations should be reviewed by fluent speakers.
- **Official contact data** (bank fraud contacts and official numbers) must be taken from each organisation's official site, with the source URL recorded.
- Kavach **supports** the authorities (1930, cybercrime.gov.in, Chakshu, RBI Sachet) and does not replace them.
- The prototype's verdicts can be wrong. A low-risk result does not prove that a message, link, or app is safe.

---

## 9. Team

| Member | Role | Owns |
| --- | --- | --- |
| **A.Krishna Mohan** | Backend and messaging integration | Telegram webhook and bot flows, language service, Golden Hour Responder, Report Router, evidence PDF, deployment |
| **Vani Karre** | AI and threat analysis | Dataset, Scam Check engine, link checks, OCR, APK scanner, Scam Bait Verifier, Scam Pulse, evaluation |
| **Dhanushiya S** | Voice, web, and pitch lead | Call Shield, X-Ray Simulator, React web app, web API, pitch and demo |

---

*Kavach is a hackathon prototype. If you have lost money to a scam, call **1930** immediately and file a complaint at **cybercrime.gov.in**.*
