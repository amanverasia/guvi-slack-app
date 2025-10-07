import os, requests
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()
app = App(token=os.environ["SLACK_BOT_TOKEN"])

OWM_BASE = "https://api.openweathermap.org"
OWM_KEY = os.environ["OPENWEATHER_API_KEY"]

def geocode_city(q: str):
    # Docs: https://openweathermap.org/api/geocoding-api
    r = requests.get(f"{OWM_BASE}/geo/1.0/direct",
                     params={"q": q, "limit": 1, "appid": OWM_KEY},
                     timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data:
        return None
    d = data[0]
    return {"name": d.get("name", q),
            "country": d.get("country",""),
            "lat": d["lat"], "lon": d["lon"]}

def current_weather(lat: float, lon: float, units="metric"):
    # Docs: https://openweathermap.org/api  (Current Weather Data)
    r = requests.get(f"{OWM_BASE}/data/2.5/weather",
                     params={"lat": lat, "lon": lon, "appid": OWM_KEY, "units": units},
                     timeout=10)
    r.raise_for_status()
    return r.json()

def format_weather(place, wx):
    desc = (wx.get("weather", [{}])[0].get("description", "") or "").title()
    t = wx.get("main", {})
    wind = wx.get("wind", {})
    return {
        "response_type": "in_channel",
        "blocks": [{
            "type": "section",
            "text": {"type": "mrkdwn",
                     "text": (
                         f"*{place['name']}, {place['country']}*\n"
                         f"{desc}\n"
                         f"🌡️ {t.get('temp')}°C (feels {t.get('feels_like')}°C) · "
                         f"💧 {t.get('humidity')}%\n"
                         f"🌬️ {wind.get('speed')} m/s"
                     )}
        }]
    }

@app.command("/weather")
def weather_cmd(ack, respond, command, logger):
    ack()
    text = (command.get("text") or "").strip()
    if not text:
        respond("Usage: `/weather <city>`  e.g., `/weather delhi`")
        return
    try:
        place = geocode_city(text)
        if not place:
            respond(f"Couldn't find `{text}`.")
            return
        wx = current_weather(place["lat"], place["lon"], units="metric")
        respond(format_weather(place, wx))
    except Exception:
        logger.exception("weather error")
        respond("Sorry, I couldn't fetch the weather right now. Please try again.")

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
