import requests
from bs4 import BeautifulSoup
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import hashlib
import time

# -----------------------------
# دالة تشفير AES/CBC/PKCS7
# -----------------------------
def encrypt_aes_cbc(message, password):
    key = hashlib.sha256(password.encode('utf-8')).digest()
    iv = bytes([0]*16)  # IV ثابت
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(message.encode('utf-8'), AES.block_size))
    encoded = base64.b64encode(ciphertext).decode('utf-8')
    return encoded

# -----------------------------
# دالة تحديث المنشور
# -----------------------------
def update_facebook_post(encrypted_json, access_token, post_id):
    payload = {
        "message": encrypted_json,
        "access_token": access_token
    }
    fb_url = f"https://graph.facebook.com/v17.0/{post_id}"
    response = requests.post(fb_url, data=payload)
    if response.status_code == 200:
        print("✅ المنشور تم تعديله بنجاح بنفس JSON المشفر")
    else:
        print("❌ خطأ في تعديل المنشور:", response.text)

# -----------------------------
# معلومات فيسبوك
# -----------------------------
ACCESS_TOKEN = "EAAnpHaKS0ZAsBQGnFzMdPXgJl7WOHrhDvRchIECkxD6VuZBLMHYJcQEv9CHfsyPQTAcGXEPvSG1wsQZA3grOZBWTe7z434cxvkjjFGPiAVZBCJvlMnRKbK2d059sSbKcG3Khle9D8J01rLRm97zEQs8G6q7i6vULeU0rLyjt03vgglGmxWlaXq59pN66kKvmTcZC4w"
POST_ID = "760975953758391_122155135934908910"
PASSWORD = "mohamed"

# -----------------------------
# حلقة لا نهائية لتحديث كل ساعة
# -----------------------------
while True:
    try:
        print("⏳ بدء التحديث...")

        # -----------------------------
        # 1️⃣ سحب المباريات من elkora
        # -----------------------------
        url = "https://www.elkora.ma/today?match_day=today"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        matches_data = []

        for match in soup.select("div.ebs-match"):
            home_team_span = match.select_one(".ebs-team.home span")
            away_team_span = match.select_one(".ebs-team.away span")
            
            home_team_name = home_team_span.get_text(strip=True) if home_team_span else ""
            away_team_name = away_team_span.get_text(strip=True) if away_team_span else ""

            home_img_tag = match.select_one(".ebs-team.home img")
            away_img_tag = match.select_one(".ebs-team.away img")

            home_img = home_img_tag["src"] if home_img_tag else ""
            away_img = away_img_tag["src"] if away_img_tag else ""

            score_tag = match.select_one(".ebs-score")
            score_text = score_tag.get_text(strip=True) if score_tag else ""

            status_tag = match.select_one(".match-status")
            time_tag = match.select_one(".ebs-match-time")
            match_status = status_tag.get_text(strip=True) if status_tag else ""
            match_time = time_tag.get_text(strip=True).replace(match_status, "") if time_tag else ""

            if match_status == "مجدولة":
                match_status = "لم تبدأ بعد"

            matches_data.append({
                "image1": home_img,
                "name1": home_team_name,
                "image2": away_img,
                "name2": away_team_name,
                "score": score_text,
                "time": match_time,
                "status": match_status
            })

        # تحويل القائمة إلى JSON
        matches_json = json.dumps(matches_data, ensure_ascii=False, indent=4)
        print("✅ JSON المباريات جاهز")

        # -----------------------------
        # 2️⃣ تشفير JSON
        # -----------------------------
        encrypted_json = encrypt_aes_cbc(matches_json, PASSWORD)
        print("✅ JSON مشفر جاهز")

        # -----------------------------
        # 3️⃣ تعديل منشور فيسبوك
        # -----------------------------
        update_facebook_post(encrypted_json, ACCESS_TOKEN, POST_ID)

        # -----------------------------
        # 4️⃣ انتظار ساعة قبل التكرار
        # -----------------------------
        print("⏰ الانتظار ساعة قبل التحديث القادم...")
        time.sleep(3600)  # 3600 ثانية = ساعة

    except Exception as e:
        print("❌ حدث خطأ:", e)
        print("⏳ إعادة المحاولة بعد دقيقة...")
        time.sleep(60)  # انتظار دقيقة قبل المحاولة مرة أخرى
