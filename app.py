# app.py
from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

app = Flask(__name__)

URL = "https://jdwel.com/today/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

cached_data = None
last_update = None
UPDATE_INTERVAL = timedelta(minutes=5)

def normalize_src(src, base="https://jdwel.com"):
    if not src:
        return ""
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        return base.rstrip("/") + src
    return src

def clean_name(txt: str) -> str:
    txt = re.sub(r"(صفحة المباراة|باقي على المباراة.*|لم تبدأ|انتهت|مباشر|LIVE)", "", txt, flags=re.I)
    txt = re.sub(r"\d+", "", txt)
    return txt.strip(" -–—: ")

def extract_today_matches():
    try:
        res = requests.get(URL, headers=HEADERS, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
    except:
        return []

    results = []
    seen = set()

    # البحث عن كل مسابقات اليوم
    competitions = soup.select(".comp_matches_list.matches_list")
    for comp in competitions:
        league_title_el = comp.select_one(".comp_separator .title")
        league_title = league_title_el.get_text(strip=True) if league_title_el else ""

        if not league_title:
            continue

        match_blocks = comp.select(".single_match")
        for block in match_blocks:
            # أسماء الفرق
            home_el = block.select_one(".hometeam .the_team")
            away_el = block.select_one(".awayteam .the_team")
            if not home_el or not away_el:
                continue
            home = clean_name(home_el.get_text(strip=True))
            away = clean_name(away_el.get_text(strip=True))

            # شعارات الفرق
            logo_home_el = block.select_one(".hometeam img.team_logo")
            logo_away_el = block.select_one(".awayteam img.team_logo")
            logo_home = normalize_src(logo_home_el.get("src")) if logo_home_el else ""
            logo_away = normalize_src(logo_away_el.get("src")) if logo_away_el else ""

            # الحالة
            status_span = block.select_one(".match_status .status_box span")
            status = status_span.get_text(strip=True) if status_span else "غير معروف"

            # الوقت الدقيق
            otime_span = block.select_one(".the_otime")
            if otime_span:
                time_ = otime_span.get_text(strip=True).split(" ")[1] + ":00"
            else:
                # fallback إلى الوقت الظاهر
                time_span = block.select_one(".the_time")
                if time_span:
                    t = time_span.get_text(strip=True)
                    # تحويل صيغة 2:00 م إلى 24 ساعة
                    try:
                        dt = datetime.strptime(t, "%I:%M %p")
                        time_ = dt.strftime("%H:%M:%S")
                    except:
                        time_ = ""
                else:
                    time_ = ""

            # القناة والمعلق
            channel = ""
            commentator = ""
            match_channels = block.select_one(".match_channels .channel_box")
            if match_channels:
                ch_el = match_channels.select_one(".channel")
                cm_el = match_channels.select_one(".commentators")
                channel = ch_el.get_text(strip=True) if ch_el else ""
                commentator = cm_el.get_text(strip=True) if cm_el else ""

            # مفتاح لتفادي التكرار
            key = f"{league_title}-{home}-{away}-{time_}"
            if key in seen:
                continue
            seen.add(key)

            results.append({
                "league": league_title,
                "home": home,
                "away": away,
                "time": time_,
                "status": status,
                "logohome": logo_home,
                "logoaway": logo_away,
                "commentator": commentator,
                "channel": channel
            })

    return results

def get_cached_matches():
    global cached_data, last_update
    now = datetime.now()
    if cached_data is None or last_update is None or now - last_update > UPDATE_INTERVAL:
        cached_data = extract_today_matches()
        last_update = now
    if not cached_data:
        return [{"league":"","home":"","away":"","time":"","status":"","logohome":"","logoaway":"","commentator":"","channel":""}]
    return cached_data

@app.route("/api/abwjdan", methods=["GET"])
def api_matches():
    matches = get_cached_matches()
    return jsonify(matches)

if __name__ == "__main__":
    app.run(debug=True)
