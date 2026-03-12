import requests
import yt_dlp
from flask import Flask, request

app = Flask(__name__)

PAGE_ACCESS_TOKEN = "EAAnpHaKS0ZAsBQ8Vp5Uvf7KM6hwcpL3J21JK9OzQ3aP9dnYqfPokgPV6hc5IG0LC2ZCiTWGkc5w2ijpcqD3jdlmZAcwlj6owIZB06ZBglKNVXNBVkk3eDTQmMyraKKj1SnGZBUUrl3uMHQ1KKT0J8Io6nNNL5SLZCEwTcpoN4vTzq3dZBXZCFzXHSA3ne13dI1XQGjAkuZBZATR"
VERIFY_TOKEN = "ABCD1211113224"


# ===============================
# استخراج الفيديو
# ===============================

def extract_video(url):

    ydl_opts = {
        "format": "best",
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=False)

        video_url = info.get("url")

    return video_url


# ===============================
# VERIFY WEBHOOK
# ===============================

@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Forbidden", 403


# ===============================
# RECEIVE MESSAGES
# ===============================

@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    if data.get("object") == "page":

        for entry in data.get("entry", []):

            for messaging_event in entry.get("messaging", []):

                sender_id = messaging_event["sender"]["id"]

                if "message" in messaging_event:

                    message = messaging_event["message"]

                    if "text" in message:

                        text = message["text"]

                        if "http" in text:

                            send_text(sender_id, "⏳ جاري تحميل الفيديو...")

                            try:

                                video = extract_video(text)

                                send_video(sender_id, video)

                            except:

                                send_text(sender_id, "❌ لم أستطع تحميل الفيديو")

                        else:

                            send_text(sender_id, "📩 أرسل رابط فيديو من أي منصة")

    return "ok", 200


# ===============================
# SEND TEXT
# ===============================

def send_text(uid, text):

    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    payload = {
        "recipient": {"id": uid},
        "message": {"text": text}
    }

    requests.post(url, json=payload)


# ===============================
# SEND VIDEO
# ===============================

def send_video(uid, video_url):

    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    payload = {
        "recipient": {"id": uid},
        "message": {
            "attachment": {
                "type": "video",
                "payload": {
                    "url": video_url
                }
            }
        }
    }

    requests.post(url, json=payload)


# ===============================
# RUN SERVER
# ===============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
