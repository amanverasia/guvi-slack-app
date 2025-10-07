# Slack Weather & Utilities Bot (Socket Mode)

Develop locally **behind a firewall** — no Flask, no ngrok, no inbound HTTP.  
We use **Slack Bolt for Python (Socket Mode)** so Slack delivers slash-command payloads over a WebSocket your app opens outbound.

---

## Features (slash commands)

- `/hello` — sanity check that the bot is alive
- `/echo <text>` — echoes text back (ephemeral reply)
- `/reverse <text>` — reverses text
- `/calc <expr>` — safe mini-calculator (supports + - * / % ** and unary +/-)
- `/time [IANA_TZ]` — current time (defaults to `Asia/Kolkata` if omitted)
- `/weather <city>` — current weather via OpenWeather (e.g., `/weather delhi`)
- `/help` — shows a command menu

---

## Prerequisites

- **Python 3.10+**
- Slack workspace where you can install custom apps
- OpenWeather account (free tier is fine) for an **API key**

> If you run Windows and see timezone errors, add: `pip install tzdata`.

---

## 1) Create your Slack App

1. Go to Slack’s app dashboard → **Create New App** (From scratch).
2. **Enable Socket Mode**:  
   - App → **Settings → Socket Mode** → toggle **On**.  
   - Create an **App-Level Token** with scope `connections:write` (token starts with `xapp-…`).
3. **OAuth & Permissions**:  
   - Under **Bot Token Scopes**, add:
     - `commands`
     - `chat:write`
   - **Install to Workspace** (or Reinstall after changes) → copy **Bot User OAuth Token** (`xoxb-…`).
4. **Slash Commands** (Features → Slash Commands): create the following commands:
   - `/hello`
   - `/echo`
   - `/reverse`
   - `/calc`
   - `/time`
   - `/weather` (usage hint: `<city>`, e.g., `delhi`)
   
   > With **Socket Mode**, you do **not** need Request URLs. Slack routes via the WebSocket.

---

## 2) OpenWeather API Key

- Sign in to OpenWeather → copy your **API key**.
- We use:
  - **Direct Geocoding**: `/geo/1.0/direct?q=City&limit=1&appid=KEY`
  - **Current Weather Data**: `/data/2.5/weather?lat=..&lon=..&units=metric&appid=KEY`
- Units can be `metric`, `imperial`, or `standard`. This bot defaults to `metric` (°C).

---

## 3) Project Setup

Create files:

```

.
├─ main.py
├─ requirements.txt
└─ .env

```

**requirements.txt**
```

slack-bolt>=1.19,<2.0
python-dotenv>=1.0
requests>=2.32
tzdata; platform_system=="Windows"

```

**.env**
```

SLACK_APP_TOKEN=xapp-your-app-level-token    # from App-Level Tokens (Socket Mode), scope: connections:write
SLACK_BOT_TOKEN=xoxb-your-bot-token          # from OAuth & Permissions after install
OPENWEATHER_API_KEY=your-openweather-key     # from OpenWeather
DEFAULT_TIMEZONE=Asia/Kolkata                # optional; used by /time when no tz is provided

````

Install dependencies:

```bash
pip install -r requirements.txt
````

---

## 4) Run

```bash
python main.py
```

You should see logs indicating the Socket Mode connection succeeded.

Now, in Slack, try:

```
/hello
/echo hello world
/reverse stressed
/calc 12.5 * 3 + 2
/time
/time Europe/London
/weather delhi
/help
```

---

## 5) Security Notes

* **Never** hardcode tokens; keep them in environment variables or `.env` (not checked into source control).
* Rotate tokens if leaked. Use read-only scopes unless you truly need more.

---

## 6) Troubleshooting

* **Slash command says timeout/failed**: Ensure the process is running and each handler calls `ack()` quickly.
* **No responses**: Confirm the app is installed in the workspace/channel and the same workspace you’re testing in.
* **Weather errors**: Verify your OpenWeather key and you haven’t exceeded rate limits.
* **Timezone errors on Windows**: `pip install tzdata` and keep `DEFAULT_TIMEZONE` set.

---

## 7) Next Ideas

* `/weather <city> --units f` to switch to Fahrenheit (`imperial`)
* `/forecast <city>` using OpenWeather’s forecast APIs
* Add richer Block Kit formatting & attachments

Happy hacking! 🌤️