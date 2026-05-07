from flask import Flask, request
import requests
import yt_dlp

app = Flask(__name__)

PAGE_ACCESS_TOKEN = "EAAnpHaKS0ZAsBRQsv1aN1TEJNlR56D2jH12PWu99bUEbZCuHZB5ukZAZCodXcGmgi9en7b4f79JZCL634eT7bXzY4WuqLzUh9rmzdmghZCQPJoDJr7m9eUjGofZCcDNYVyVmLp9uYz4mtp5bvtYWjFqJXMiSGub3Sn8R9R8KULwoHmK8q13hf6eXKV53qlFaefiF8u2hCg2kBAZDZD"
VERIFY_TOKEN = "VERIFY_TOKEN"

processed = set()  # لمنع التكرار

def send_message(psid, text):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    requests.post(url, json={
        "recipient": {"id": psid},
        "message": {"text": text}
    })

def send_video(psid, url_video):
    api = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

    payload = {
        "recipient": {"id": psid},
        "message": {
            "attachment": {
                "type": "video",
                "payload": {
                    "url": url_video,
                    "is_reusable": True
                }
            }
        }
    }

    requests.post(api, json=payload)

def get_video_url(link):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'worst[ext=mp4][acodec!=none]/worst'  # 🔥 صوت + فيديو
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)

        # نجيب أول format صالح فيه audio
        for f in info.get("formats", []):
            if f.get("url") and f.get("acodec") != "none" and f.get("vcodec") != "none":
                return f["url"]

        return None

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "error"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):

            sender = event["sender"]["id"]

            msg = event.get("message", {})
            msg_id = msg.get("mid")

            # 🔴 منع التكرار
            if msg_id in processed:
                continue

            processed.add(msg_id)

            text = msg.get("text")

            if not text:
                continue

            if text.startswith("http"):

                send_message(sender, "⬇️ يتم تحميل على سيرفر لان ")

                try:
                    video_url = get_video_url(text)

                    if not video_url:
                        send_message(sender, "❌ ما لقيتش فيديو صالح")
                        continue

                    send_message(sender, "⬆️تم تحميل يتم ارسال لان ")
                    send_video(sender, video_url)

                except Exception as e:
                    send_message(sender, f"❌ خطأ: {str(e)}")

            else:
                send_message(sender, "مرحبا قوم بي ارسال رابط فيديو من facebook/instagram/youtube/tik tok 😁")

    return "ok"

if __name__ == "__main__":

    print("Bot Running...")

    app.run(host="0.0.0.0", port=13833)
