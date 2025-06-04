from fastapi import APIRouter
from typing import List
import requests
from datetime import datetime, timedelta

router = APIRouter()

def get_eonet_events(days: int = 1):
    base_url = "https://eonet.gsfc.nasa.gov/api/v3"
    start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    response = requests.get(f"{base_url}/events", params={"start": start_date})
    if response.status_code != 200:
        return []
    events = response.json().get("events", [])
    event_list = []
    for event in events:
        event_list.append({
            "id": event["id"],
            "title": event["title"],
            "type": event["categories"][0]["title"],
            "coordinates": event["geometry"][0]["coordinates"],
            "date": event["geometry"][0]["date"],
            "source": event["sources"][0]["url"] if event["sources"] else None,
            "status": event.get("status", "Unknown")
        })
    return event_list

@router.get("/eonet-events", response_model=List[dict])
def eonet_events_route(days: int = 1):
    return get_eonet_events(days)