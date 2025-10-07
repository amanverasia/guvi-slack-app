import os, ast, operator as op
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# allow only these operators / numbers
OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.Mod: op.mod, ast.Pow: op.pow, ast.USub: op.neg, ast.UAdd: op.pos,
}
def safe_eval(expr: str):
    def _eval(node):
        if isinstance(node, ast.Num):  # 3.8 and earlier
            return node.n
        if isinstance(node, ast.Constant):  # py3.8+
            if isinstance(node.value, (int, float)): return node.value
            raise ValueError("only numbers allowed")
        if isinstance(node, ast.BinOp):
            return OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            return OPS[type(node.op)](_eval(node.operand))
        raise ValueError("unsupported expression")
    tree = ast.parse(expr, mode="eval")
    return _eval(tree.body)

load_dotenv()
app = App(token=os.environ["SLACK_BOT_TOKEN"])

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

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
