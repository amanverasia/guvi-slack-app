import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()
app = App(token=os.environ["SLACK_BOT_TOKEN"])

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

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
