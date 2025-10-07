import os
import ast
import operator as op
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+; on Windows, install tzdata
import requests
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ----------------------------
# Environment & App Init
# ----------------------------
load_dotenv()

SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")      # xapp-...
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")      # xoxb-...
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
DEFAULT_TZ = os.environ.get("DEFAULT_TIMEZONE", "Asia/Kolkata")

if not SLACK_APP_TOKEN or not SLACK_BOT_TOKEN:
    raise SystemExit("Missing SLACK_APP_TOKEN and/or SLACK_BOT_TOKEN in environment (.env).")

app = App(token=SLACK_BOT_TOKEN)

# ----------------------------
# Utilities
# ----------------------------

# Safe arithmetic: allow numbers and + - * / % ** and unary +/- only
OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.Mod: op.mod, ast.Pow: op.pow, ast.USub: op.neg, ast.UAdd: op.pos
}

def safe_eval(expr: str):
    """Safely evaluate a simple arithmetic expression."""
    def _eval(node):
        if isinstance(node, ast.Constant):  # py3.8+
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("only numbers allowed")
        if hasattr(ast, "Num") and isinstance(node, ast.Num):  # legacy
            return node.n
        if isinstance(node, ast.BinOp):
            if type(node.op) not in OPS:
                raise ValueError("unsupported operator")
            return OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            if type(node.op) not in OPS:
                raise ValueError("unsupported operator")
            return OPS[type(node.op)](_eval(node.operand))
        raise ValueError("unsupported expression")
    tree = ast.parse(expr, mode="eval")
    return _eval(tree.body)

OWM = "https://api.openweathermap.org"

def geocode_city(q: str):
    """OpenWeather Direct Geocoding: city -> lat/lon."""
    if not OPENWEATHER_API_KEY:
        raise RuntimeError("OPENWEATHER_API_KEY is not set.")
    r = requests.get(f"{OWM}/geo/1.0/direct",
                     params={"q": q, "limit": 1, "appid": OPENWEATHER_API_KEY},
                     timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data:
        return None
    d = data[0]
    return {
        "name": d.get("name", q),
        "country": d.get("country", ""),
        "lat": d["lat"],
        "lon": d["lon"]
    }

def current_weather(lat: float, lon: float, units: str = "metric"):
    """OpenWeather Current Weather Data by lat/lon."""
    r = requests.get(f"{OWM}/data/2.5/weather",
                     params={"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY, "units": units},
                     timeout=10)
    r.raise_for_status()
    return r.json()

def format_weather_block(place: dict, wx: dict):
    desc = (wx.get("weather", [{}])[0].get("description", "") or "").title()
    t = wx.get("main", {})
    wind = wx.get("wind", {})
    lines = [
        f"*{place['name']}, {place.get('country','')}*",
        f"{desc}",
        f"🌡️ {t.get('temp')}°C (feels {t.get('feels_like')}°C)  ·  💧 {t.get('humidity')}%",
        f"🌬️ {wind.get('speed')} m/s",
    ]
    return {
        "response_type": "in_channel",
        "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(lines)}}]
    }

# ----------------------------
# Slash Commands
# ----------------------------

@app.command("/hello")
def hello_cmd(ack, respond, command):
    ack()
    user = command.get("user_name", "there")
    respond(f"👋 Hey, {user}! I’m alive. Try `/help`")

@app.command("/echo")
def echo_cmd(ack, respond, command):
    ack()
    text = (command.get("text") or "").strip()
    if not text:
        respond("Usage: `/echo your text`")
    else:
        respond({"response_type": "ephemeral", "text": f"you said: {text}"})

@app.command("/reverse")
def reverse_cmd(ack, respond, command):
    ack()
    text = (command.get("text") or "").strip()
    if not text:
        respond("Usage: `/reverse your text`")
    else:
        respond(text[::-1])

@app.command("/calc")
def calc_cmd(ack, respond, command):
    ack()
    expr = (command.get("text") or "").strip()
    if not expr:
        respond("Usage: `/calc 12.5 * 3 + 2`")
        return
    try:
        result = safe_eval(expr)
        respond(f"🧮 `{expr}` = *{result}*")
    except Exception:
        respond("Sorry, I only support basic numeric expressions like `2+2*3`, `-4.5**2`, `7%3`")

@app.command("/time")
def time_cmd(ack, respond, command):
    ack()
    tz_name = (command.get("text") or DEFAULT_TZ).strip() or DEFAULT_TZ
    try:
        now = datetime.now(ZoneInfo(tz_name))
        respond(f"🕒 *{tz_name}*: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception:
        respond("Unknown timezone. Try `/time Asia/Kolkata` or `/time Europe/London`")

@app.command("/weather")
def weather_cmd(ack, respond, command, logger):
    ack()
    query = (command.get("text") or "").strip()
    if not query:
        respond("Usage: `/weather <city>`  e.g., `/weather delhi`")
        return
    try:
        place = geocode_city(query)
        if not place:
            respond(f"Couldn't find `{query}`.")
            return
        wx = current_weather(place["lat"], place["lon"], units="metric")
        respond(format_weather_block(place, wx))
    except Exception:
        logger.exception("weather error")
        respond("Sorry, I couldn't fetch the weather right now. Please try again.")

@app.command("/help")
def help_cmd(ack, respond, command):
    ack()
    respond({
        "response_type": "ephemeral",
        "blocks": [
            {"type":"section","text":{"type":"mrkdwn","text":
             "*Available commands:*\n"
             "• `/hello` – sanity check\n"
             "• `/echo <text>` – echo back (ephemeral)\n"
             "• `/reverse <text>` – reverse text\n"
             "• `/calc <expr>` – safe math (e.g., `12.5*3+2`, `-4.5**2`)\n"
             "• `/time [IANA_TZ]` – current time (default Asia/Kolkata)\n"
             "• `/weather <city>` – current weather via OpenWeather\n"
             "• `/help` – this menu\n"}}
        ]
    })

# ----------------------------
# Entry
# ----------------------------
if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    print("Connecting to Slack via Socket Mode...")
    handler.start()