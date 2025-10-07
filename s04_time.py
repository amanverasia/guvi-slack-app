import os
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()
app = App(token=os.environ["SLACK_BOT_TOKEN"])

@app.command("/time")
def time_cmd(ack, respond, command):
    ack()
    # default to Asia/Kolkata; allow custom tz: /time Europe/London
    tz_name = (command.get("text") or "Asia/Kolkata").strip()
    try:
        now = datetime.now(ZoneInfo(tz_name))
        respond(f"🕒 *{tz_name}*: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception:
        respond("Unknown timezone. Try `/time Asia/Kolkata` or `/time Europe/London`")

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
