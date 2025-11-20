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
        return "تيك"
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("/"):
        return base.rstrip("/") + src
    return src

def clean_name(txt: str) -> str:
    txt = re.sub(r"(صفحة المباراة|باقي على المباراة.*|لم تبدأ|انتهت|مباشر|LIVE)", "", txt, flags=re.I)
    txt = re.sub(r"\d+", "", txt)
    txt = txt.strip(" -–—: ")
    return txt if txt else "تيك"

def extract_today_matches():
    try:
        res = requests.get(URL, headers=HEADERS, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
    except:
        return []

    results = []
    seen = set()

    leagues = soup.select("section, .mec-container, .elementor-widget-wrap, div")

    for league_block in leagues:
        league_title = ""
        title_el = league_block.find(["h2", "h3", "h4", "h5"])
        if title_el:
            league_title = title_el.get_text(strip=True)
        if not league_title or len(league_title) < 3:
            continue

        match_blocks = league_block.select(".mec-row, .match-item, li, .mec, .mec-table")
        for block in match_blocks:
            txt = block.get_text(" ", strip=True)
            if not txt:
                continue

            today_str = datetime.now().strftime("%Y-%m-%d")
            if today_str not in txt and re.search(r"\d{4}-\d{2}-\d{2}", txt):
                continue

            time_match = re.search(r"\b([01]?\d|2[0-3]):[0-5]\d\b", txt)
            time_ = (time_match.group(0) + ":00") if time_match else "تيك"

            if "انتهت" in txt:
                status = "انتهت"
            elif "لم تبدأ" in txt:
                status = "لم تبدأ"
            elif "مباشر" in txt or "Live" in txt:
                status = "جارية"
            else:
                status = "تيك"

            imgs = [normalize_src(img.get("src")) for img in block.find_all("img") if img.get("src")]
            logo_home = imgs[0] if len(imgs) > 0 else "تيك"
            logo_away = imgs[1] if len(imgs) > 1 else "تيك"

            parts = re.split(r"\s+vs\.?\s+|\s+مقابل\s+|\s+[-–—:]\s+", txt)
            parts = [clean_name(p) for p in parts if p.strip()]
            home, away = parts[0] if len(parts) >= 1 else "تيك", parts[1] if len(parts) >= 2 else "تيك"

            channel = block.select_one(".match_channels .channel")
            channel = channel.get_text(strip=True) if channel else "تيك"

            commentator = block.select_one(".match_channels .commentators")
            commentator = commentator.get_text(strip=True).replace("mic","").strip() if commentator else "تيك"

            key = f"{league_title}-{home}-{away}-{time_}"
            if key in seen:
                continue
            seen.add(key)

            results.append({
                "league": league_title if league_title else "تيك",
                "home": home,
                "away": away,
                "time": time_,
                "status": status,
                "logohome": logo_home,
                "logoaway": logo_away,
                "channel": channel,
                "commentator": commentator
            })

    return results

def get_cached_matches():
    global cached_data, last_update
    now = datetime.now()
    if cached_data is None or last_update is None or now - last_update > UPDATE_INTERVAL:
        cached_data = extract_today_matches()
        last_update = now
    if not cached_data:
        return [{"league":"تيك","home":"تيك","away":"تيك","time":"تيك",
                 "status":"تيك","logohome":"تيك","logoaway":"تيك",
                 "channel":"تيك","commentator":"تيك"}]
    return cached_data

# ==== Vercel handler ====
def handler(request, *args, **kwargs):
    matches = get_cached_matches()
    return jsonify(matches)
