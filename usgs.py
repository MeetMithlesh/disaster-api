from fastapi import APIRouter
from typing import List
import requests
import pandas as pd

router = APIRouter()

def get_usgs_earthquakes():
    URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    response = requests.get(URL)
    data = response.json()
    earthquake_list = []
    for feature in data["features"]:
        properties = feature["properties"]
        geometry = feature["geometry"]
        timestamp = properties["time"]
        datetime_obj = pd.to_datetime(timestamp, unit="ms")
        earthquake_list.append({
            "time": datetime_obj.isoformat(),
            "magnitude": properties["mag"],
            "magType": properties["magType"],
            "place": properties["place"],
            "longitude": geometry["coordinates"][0],
            "latitude": geometry["coordinates"][1],
            "depth_km": geometry["coordinates"][2],
            "tsunami_alert": properties.get("tsunami", 0),
            "type": properties["type"],
            "title": properties["title"]
        })
    return earthquake_list

@router.get("/usgs-earthquakes", response_model=List[dict])
def usgs_earthquakes_route():
    return get_usgs_earthquakes()