from fastapi import APIRouter
from typing import List
import requests
from datetime import datetime

router = APIRouter()

def fetch_gdacs_disasters():
    gdacs_url = "https://www.gdacs.org/xml/rss.xml"
    response = requests.get(gdacs_url)
    if response.status_code == 200:
        from xml.etree import ElementTree as ET
        root = ET.fromstring(response.content)
        disasters = []
        for item in root.findall(".//item"):
            title = item.find("title").text
            link = item.find("link").text
            pub_date = item.find("pubDate").text
            disasters.append({"source": "GDACS", "disaster": title, "date": pub_date, "details": link})
        return disasters
    else:
        return []

def fetch_nasa_disasters():
    api_key = "e206087e-3ead-4a0e-86b4-274aec9eff03"
    nasa_url = f"https://eonet.gsfc.nasa.gov/api/v3/events?api_key={api_key}"
    response = requests.get(nasa_url)
    if response.status_code == 200:
        data = response.json()
        disasters = []
        for event in data["events"]:
            title = event["title"]
            event_type = event["categories"][0]["title"]
            date = event["geometry"][0]["date"]
            formatted_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
            link = event["sources"][0]["url"]
            disasters.append({"source": "NASA", "disaster": f"{event_type}: {title}", "date": formatted_date, "details": link})
        return disasters
    else:
        return []

@router.get("/gdacs-nasa", response_model=List[dict])
def gdacs_nasa_route():
    gdacs_data = fetch_gdacs_disasters()
    nasa_data = fetch_nasa_disasters()
    return gdacs_data + nasa_data