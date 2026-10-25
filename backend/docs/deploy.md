# Kavach backend deployment

This guide deploys the backend using the Telegram bot webhook.

## Requirements

- Ubuntu or Debian VM with Python 3.11 or newer
- A domain pointed to the VM with public HTTPS
- Git and Nginx
- A Telegram bot token
- A random Telegram webhook secret

## Install the backend

Check out the approved project version under `/opt/kavach`. Then install the backend:

```bash
cd /opt/kavach/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[voice]"
```

The `voice` extra is optional. Omit it and use `python -m pip install -e .` if voice-note support is not needed.

## Create the service account and data directory

Create the service account once. Skip the `useradd` command if it already exists:

```bash
sudo useradd --system --home-dir /var/lib/kavach --create-home --shell /usr/sbin/nologin kavach
sudo install -d -o kavach -g kavach /var/lib/kavach/files
```

## Configure the environment

From the backend directory, create `.env` from the example if it does not already exist:

```bash
cd /opt/kavach/backend
cp .env.example .env
nano .env
```

Set the production values in `.env`:

```dotenv
APP_ENV=production
DATABASE_PATH=/var/lib/kavach/kavach.db
FILES_DIR=/var/lib/kavach/files
DRY_RUN=0

WHATSAPP_PROVIDER=telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_WEBHOOK_SECRET=your-random-webhook-secret

HASH_SALT=your-random-secret-value
```

Generate a random value for each of `HASH_SALT` and `TELEGRAM_WEBHOOK_SECRET`:

```bash
openssl rand -hex 32
```

Use a different generated value for each setting. Keep `.env` private and out of Git.

Set any analysis-provider keys required by the deployed features, following `.env.example`.

Allow the service account to read the environment file and write its data:

```bash
sudo chown kavach:kavach /opt/kavach/backend/.env
sudo chmod 600 /opt/kavach/backend/.env
sudo chown -R kavach:kavach /var/lib/kavach
```

## Configure Nginx and HTTPS

Configure Nginx to proxy requests to the local backend at `http://127.0.0.1:8000`. Set the domain name in the Nginx server configuration and enable HTTPS with a valid TLS certificate.

The public backend URL must be reachable over HTTPS before setting the Telegram webhook.

## Run Kavach with systemd

Create `/etc/systemd/system/kavach.service` with:

```ini
[Unit]
Description=Kavach backend
After=network-online.target
Wants=network-online.target

[Service]
User=kavach
Group=kavach
WorkingDirectory=/opt/kavach/backend
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/kavach/backend/.venv/bin/uvicorn kavach.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now kavach
sudo systemctl status kavach
```

View service logs with:

```bash
sudo journalctl -u kavach -f
```

## Set the Telegram webhook

After the backend is running and HTTPS is configured, the webhook URL should be:

```text
https://your-domain.example/webhook/telegram
```

Enter the bot token and webhook secret when prompted, then run:

```bash
read -rsp "Telegram bot token: " TELEGRAM_BOT_TOKEN
printf '\n'
read -rsp "Telegram webhook secret: " TELEGRAM_WEBHOOK_SECRET
printf '\n'

curl --fail-with-body --silent --show-error --request POST \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  --data-urlencode "url=https://your-domain.example/webhook/telegram" \
  --data-urlencode "secret_token=${TELEGRAM_WEBHOOK_SECRET}"

unset TELEGRAM_BOT_TOKEN TELEGRAM_WEBHOOK_SECRET
```

Replace `your-domain.example` with the deployed domain. The token and secret entered at the prompts must match `TELEGRAM_BOT_TOKEN` and `TELEGRAM_WEBHOOK_SECRET` in `.env`.

## Check the deployment

Check the backend health endpoint from the VM:

```bash
curl https://your-domain.example/health
```

Check the Telegram webhook status by entering the bot token when prompted:

```bash
read -rsp "Telegram bot token: " TELEGRAM_BOT_TOKEN
printf '\n'

curl --fail-with-body --silent --show-error \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"

unset TELEGRAM_BOT_TOKEN
```