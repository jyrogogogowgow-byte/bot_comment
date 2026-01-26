from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

VERIFY_TOKEN = "my_secret_verify_token"
PAGE_ACCESS_TOKEN = "EAAnpHaKS0ZAsBQnxCc1YjIk0l2U1d6tuUl0JZBGCMzU3ZCAza4PaZBGKKn25mtlHtfcxL5sY7Fpjvu8yezyZApD3XHGAIH4jXEXGSIFRUFDqzew07QZBnjlfv8vZB0Rb9LsWaQaukyECOZAdgI44OKMdoMTxrXhn2EpWc4sZBf9ozouIF1nR1gv3n0BpRNJ5z73IOsSXzvp1lAgZDZD"

# Verification endpoint (من فيسبوك)
@app.route("/webhook", methods=["GET"])
def verify():
    token_sent = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token_sent == VERIFY_TOKEN:
        return str(challenge)
    return "Invalid verification token"

# Endpoint لاستقبال الأحداث
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            if value.get("item") == "comment":
                comment_id = value["comment_id"]
                # الرد التلقائي
                message = "شكراً على تعليقك!"
                reply_url = f"https://graph.facebook.com/v17.0/765581629976925_311300605297008/comments"
                requests.post(reply_url, data={"message": message, "access_token": PAGE_ACCESS_TOKEN})
    return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    app.run(port=5000)
