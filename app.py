from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

URL = "https://www.yallakora.com/match-center?date=12/31/2025#days"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
BASE_URL = "https://www.yallakora.com"


def get_matches():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"error": "Failed to fetch matches", "details": str(e)}

    soup = BeautifulSoup(response.text, "html.parser")
    matches = []

    for item in soup.find_all("div", {"livescorematchid": True}):
        match = {}
        match["match_id"] = item.get("livescorematchid")

        # القناة
        channel = item.find("div", class_="channel")
        match["channel"] = channel.get_text(strip=True) if channel else None

        # الجولة
        round_div = item.find("div", class_="date")
        match["round"] = round_div.get_text(strip=True) if round_div else None

        # الحالة
        status = item.find("div", class_="matchStatus")
        match["status"] = status.get_text(strip=True) if status else None

        # الوقت
        time = item.find("span", class_="time")
        match["time"] = time.get_text(strip=True) if time else None

        # الفرق
        teamA_div = item.find("div", class_="teamA")
        teamB_div = item.find("div", class_="teamB")

        match["team_a"] = {
            "name": teamA_div.find("p").get_text(strip=True) if teamA_div else None,
            "logo": teamA_div.find("img").get("src") if teamA_div else None,
            "scorers": []
        }

        match["team_b"] = {
            "name": teamB_div.find("p").get_text(strip=True) if teamB_div else None,
            "logo": teamB_div.find("img").get("src") if teamB_div else None,
            "scorers": []
        }

        # نتيجة المباراة
        result_div = item.find("div", class_="matchResult")
        if result_div:
            match["score"] = {
                "team_a": result_div.find("span", class_="a").get_text(strip=True),
                "team_b": result_div.find("span", class_="b").get_text(strip=True)
            }
        else:
            match["score"] = {"team_a": None, "team_b": None}

        # من سجل الهدف
        scorer_divs = item.find_all("div", class_="goal")
        for goal in scorer_divs:
            player = goal.find("a", class_="player")
            if player:
                player_name = player.find("span", class_="playerName").get_text(strip=True)
                player_time = player.find("span", class_="time").get_text(strip=True)
                player_link = BASE_URL + player.get("href")

                # تحديد الفريق
                parent_team_div = goal.find_parent("div", class_="team")
                if parent_team_div and "teamA" in parent_team_div.get("class", []):
                    match["team_a"]["scorers"].append({
                        "name": player_name,
                        "time": player_time,
                        "link": player_link
                    })
                else:
                    match["team_b"]["scorers"].append({
                        "name": player_name,
                        "time": player_time,
                        "link": player_link
                    })

        # الصور
        images = []
        for img in item.find_all("img"):
            src = img.get("src")
            alt = img.get("alt")
            # نتجنب شعار الفريق إذا كان موجود بالفعل
            if src not in [match["team_a"]["logo"], match["team_b"]["logo"]]:
                images.append({"src": src, "alt": alt})
        match["images"] = images

        # الروابط
        links = []
        for a in item.find_all("a", href=True):
            links.append({
                "text": a.get_text(strip=True),
                "href": BASE_URL + a["href"] if a["href"].startswith("/") else a["href"]
            })
        match["links"] = links

        matches.append(match)

    return matches


@app.route("/api/matches", methods=["GET"])
def api_matches():
    data = get_matches()
    return jsonify({
        "source": "yallakora",
        "count": len(data) if isinstance(data, list) else 0,
        "matches": data
    })


if __name__ == "__main__":
    app.run(debug=True)
