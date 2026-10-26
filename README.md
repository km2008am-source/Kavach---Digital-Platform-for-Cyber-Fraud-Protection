# Kavach — Digital Safety & Cyber Fraud Protection

Kavach is a hackathon prototype that helps people assess suspicious digital messages and find practical next steps when they encounter or experience cyber fraud.

The project includes a React web interface and a FastAPI backend. The current messaging demo uses a Telegram bot.

> **Prototype notice:** Kavach is not a bank, police service, or Government of India service. Its risk assessments can be wrong and must not be treated as proof that a message or link is safe. Never share an OTP, PIN, password, or full payment credentials with the bot.

## What it can do

- **Check suspicious content:** assess message text, links, and supported screenshots for scam indicators.
- **Explain risk signals:** combine explainable rules with optional language-model and reputation checks.
- **Read screenshots:** extract text with OCR; an optional vision provider can be configured when local Tesseract is unavailable.
- **Support a reported-loss flow:** guide a user who says they lost money through evidence collection and next steps.
- **Website, connected to the backend:** Check a message (text, links, screenshots, APK files), the scam-call Training simulator, Scam Pulse (alerts and a demo replay with `DEMO_MODE=1`), Get help, and News. News shows hand-picked articles, labelled as demo, until `NEWS_FEEDS` is set.
- **Provide a Telegram demo:** send text, a screenshot, an APK or a voice note to the configured bot to receive a check.
- **Call Shield (Twilio):** screens an unknown call by asking the caller's reason, checks the claimed organisation against official numbers, and alerts the user on the bot. Point a Twilio number's voice webhook at `/twilio/voice` and set `PUBLIC_BASE_URL`, `TWILIO_AUTH_TOKEN` and `DEMO_USER_NUMBER`.

APK scanning is a prototype feature; it was checked with the safe test APKs in `data/samples/apks/`. Follow the documented limitations.

## Project layout

~~~text
backend/                 FastAPI application, analysis pipeline, messaging flows
  kavach/analysis/        Scam analysis, rules, OCR, links, and related modules
  kavach/flows/           Conversation and incident-response flows
  kavach/whatsapp/        Messaging clients, webhooks, media handling, cleanup
  tests/                  Backend tests
web/                      React and Vite web interface
data/samples/             Sample messages and evaluation inputs
eval/                     Evaluation scripts and reports
docs/                     Deployment notes and project documentation
~~~

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

Edit backend/.env with the settings for the features you want to run. For the Telegram demo, set:

~~~dotenv
WHATSAPP_PROVIDER=telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_WEBHOOK_SECRET=your-random-webhook-secret
~~~

The .env.example includes these settings. Set WHATSAPP_PROVIDER=telegram and fill in TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET in your private .env file. Do not commit .env or real credentials. Configure analysis-provider keys from .env.example if you want those optional checks; the rule-based checks can run without an LLM key.

Start the API from the backend directory:

~~~bash
python -m uvicorn kavach.main:app --reload --port 8000
~~~

The API health endpoint is http://127.0.0.1:8000/health. FastAPI's interactive API documentation is available at http://127.0.0.1:8000/docs.

### 2. Start the web interface

Open a second terminal at the repository root:

~~~bash
cd web
npm install
npm run dev
~~~

Open the local URL printed by Vite, usually http://localhost:5173. The Vite development server proxies API, static-file, and health requests to the backend on port 8000.

### 3. Connect Telegram for local testing

Telegram webhooks require a publicly reachable HTTPS URL. For local testing, expose the backend through a trusted HTTPS tunnel, then configure the bot webhook to:

~~~text
https://your-public-host/webhook/telegram
~~~

Use the same bot token and webhook secret configured in backend/.env. The production VM, HTTPS, systemd, and webhook setup are described in [backend/docs/deploy.md](backend/docs/deploy.md).

## Run backend checks

Install the optional test dependencies and run the backend suite:

~~~bash
cd backend
python -m pip install -e ".[test]"
python -m pytest -q
~~~

The evaluation scripts and their current reports are under eval/. See the project documentation for evaluation scope and known limitations.

## Safety guidance

If money has been lost, contact your bank using its official app or website and report the incident promptly. In India, call the National Cyber Crime Helpline at **1930** or use the [National Cyber Crime Reporting Portal](https://cybercrime.gov.in/). Do not wait for Kavach to respond before taking urgent action.

Do not upload real OTPs, PINs, passwords, full card details, or other secrets. Use synthetic or redacted examples when demonstrating the project.

## Documentation

- [Backend deployment guide](backend/docs/deploy.md)
- [Analysis limitations](docs/LIMITATIONS.md)
- [Analysis work log](docs/MEMBER2_LOG.md)
- [Evaluation report](eval/report.md)

## Contributing

Use a feature branch and open a pull request against main. Keep credentials, local environment files, databases, uploaded files, and generated artifacts out of commits.
