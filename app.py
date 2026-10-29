import os, requests, base64
from flask import Flask, request
from telegram import Bot, Update

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_KEY")
CHAT_ID = os.environ.get("CHAT_ID")

bot = Bot(TELEGRAM_TOKEN)
app = Flask(__name__)

def ask_gemini(image_bytes):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    b64 = base64.b64encode(image_bytes).decode()
    body = {
      "contents": [{
        "parts": [
          {"text": "You are a 12th-grade math teacher. Read the question from the image and solve it fully, step by step. Give the final answer clearly at the end."},
          {"inline_data": {"mime_type": "image/jpeg", "data": b64}}
        ]
      }]
    }
    r = requests.post(url, json=body, timeout=90)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    if update.message and update.message.photo:
        msg = update.message
        file = bot.get_file(msg.photo[-1].file_id)
        img = file.download_as_bytearray()
        msg.reply_text("?? Solving...")
        try:
            answer = ask_gemini(bytes(img))
            # Save for ESP32 to fetch
            with open("/tmp/latest.txt", "w") as f:
                f.write(answer)
            # Send to Telegram
            bot.send_message(msg.chat_id, answer)
        except Exception as e:
            msg.reply_text(f"Error: {e}")
    return "ok", 200

@app.route("/latest")
def latest():
    try:
        with open("/tmp/latest.txt") as f:
            return f.read()
    except:
        return "No answer yet"

@app.route("/")
def home():
    return "Server running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
