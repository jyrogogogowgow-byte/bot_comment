import json
import requests
import yt_dlp
import re
import time
from flask import Flask, request

app = Flask(__name__)

PAGE_ACCESS_TOKEN = "EAASKJ7rjAZBUBRNmYyOK5IEqe3grBs5KfG1sej5ZCiGwHqZCMwfBIu8pZBWNv1JAlcSTEKUJbBRDGfz8UDM0UuurKuqSMVbt46X1i9dJNZCRyTlzlpfzlN7RXfxojZCfqJ1tR9SD5lPyHEikVl49IlRVaC7oZAoYP4vbhCpDfkvzniKhDb4ngeW0H6wbJnakzyhiFMD4rzskwZDZD"
VERIFY_TOKEN = "123456"

processed_messages = set()

# ==============================
# تشغيل / إيقاف
# ==============================
bot_enabled = True

# ==============================
# استخراج الرابط
# ==============================
def extract_url(text):
    urls = re.findall(r'(https?://[^\s]+)', text)
    return urls[0] if urls else None

# ==============================
# استخراج direct video
# ==============================
def get_direct_video(url):
    ydl_opts = {
        "quiet": True,
        "nocheckcertificate": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        if "formats" in info:
            for f in reversed(info["formats"]):
                if (
                    f.get("ext") == "mp4"
                    and f.get("acodec") != "none"
                    and f.get("vcodec") != "none"
                ):
                    return f.get("url")

        return info.get("url")

# ==============================
# إرسال رسالة
# ==============================
def send_message(user_id, text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    data = {
        "recipient": {"id": user_id},
        "message": {"text": text}
    }

    requests.post(url, json=data)

# ==============================
# إرسال فيديو من URL
# ==============================
def send_video(user_id, video_url):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    data = {
        "recipient": {"id": user_id},
        "message": {
            "attachment": {
                "type": "video",
                "payload": {
                    "url": video_url,
                    "is_reusable": True
                }
            }
        }
    }

    requests.post(url, json=data)

# ==============================
# Webhook Verification
# ==============================
@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge
    return "Error", 403

# ==============================
# Webhook الرئيسي
# ==============================
@app.route('/webhook', methods=['POST'])
def webhook():
    global bot_enabled

    data = request.json

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):

            sender_id = event.get("sender", {}).get("id")
            message = event.get("message", {})

            if not sender_id or "mid" not in message:
                continue

            # منع التكرار
            if message["mid"] in processed_messages:
                continue
            processed_messages.add(message["mid"])

            text = message.get("text", "")

            # أوامر
            if text == "/stop":
                bot_enabled = False
                send_message(sender_id, "🛑 تم إيقاف البوت")
                return "ok", 200

            if text == "/start":
                bot_enabled = True
                send_message(sender_id, "✅ تم تشغيل البوت")
                return "ok", 200

            if not bot_enabled:
                send_message(sender_id, "🛑 البوت متوقف")
                return "ok", 200

            # استخراج الرابط
            url = extract_url(text)

            if url:
                send_message(sender_id, "⏳ جاري جلب الفيديو...")

                try:
                    video_url = get_direct_video(url)

                    if not video_url:
                        send_message(sender_id, "❌ لم أستطع استخراج الفيديو")
                        return "ok", 200

                    send_video(sender_id, video_url)

                except Exception as e:
                    print(e)
                    send_message(sender_id, "❌ وقع خطأ")

            else:
                send_message(sender_id, "📩 أرسل رابط فيديو")

    return "ok", 200

# ==============================
# تشغيل السيرفر
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
