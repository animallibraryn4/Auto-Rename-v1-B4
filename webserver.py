import os, threading, subprocess, sys
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Dating Bot is running!"

def run_bot():
    subprocess.run([sys.executable, "bot.py"])

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_server()
