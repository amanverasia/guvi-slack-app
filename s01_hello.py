import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()
app = App(token=os.environ["SLACK_BOT_TOKEN"])

@app.command("/hello")
def hello_cmd(ack, respond, command):
    ack()  # must ack within 3s
    user = command.get("user_name", "there")
    respond(f"👋 Hey, {user}! I’m alive.")

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
