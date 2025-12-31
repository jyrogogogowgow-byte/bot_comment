import requests
from bs4 import BeautifulSoup

def handler(request, response):
    URL = "https://www.yallakora.com/match-center"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    resp = requests.get(URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")

    matches = []

    for item in soup.find_all("div", {"livescorematchid": True}):
        match = {}

        match["match_id"] = item.get("livescorematchid")
        channel = item.find("div", class_="channel")
        match["channel"] = channel.get_text(strip=True) if channel else None

        round_div = item.find("div", class_="date")
        match["round"] = round_div.get_text(strip=True) if round_div else None

        status = item.find("div", class_="matchStatus")
        match["status"] = status.get_text(strip=True) if status else None

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

        # روابط
        links = []
        for a in item.find_all("a", href=True):
            links.append({
                "text": a.get_text(strip=True),
                "href": a["href"]
            })
        match["links"] = links

        matches.append(match)

    # رجع JSON
    return response.json({
        "source": "yallakora",
        "count": len(matches),
        "matches": matches
    })
