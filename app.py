from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

URL = "https://www.yallakora.com/match-center"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def get_matches():
    response = requests.get(URL, headers=HEADERS, timeout=15)
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
        teamA = item.find("div", class_="teamA")
        teamB = item.find("div", class_="teamB")

        match["team_a"] = {
            "name": teamA.find("p").get_text(strip=True) if teamA else None,
            "logo": teamA.find("img").get("src") if teamA else None
        }

        match["team_b"] = {
            "name": teamB.find("p").get_text(strip=True) if teamB else None,
            "logo": teamB.find("img").get("src") if teamB else None
        }

        # الصور
        images = []
        for img in item.find_all("img"):
            images.append({
                "src": img.get("src"),
                "alt": img.get("alt")
            })

        match["images"] = images

        # الروابط
        links = []
        for a in item.find_all("a", href=True):
            links.append({
                "text": a.get_text(strip=True),
                "href": a["href"]
            })

        match["links"] = links

        matches.append(match)

    return matches


@app.route("/api/matches", methods=["GET"])
def api_matches():
    data = get_matches()
    return jsonify({
        "source": "yallakora",
        "count": len(data),
        "matches": data
    })


if __name__ == "__main__":
    app.run(debug=True)
