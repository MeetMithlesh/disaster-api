from fastapi import APIRouter
from typing import List
import requests

router = APIRouter()

def get_noaa_alerts():
    noaa_url = "https://api.weather.gov/alerts/active"
    noaa_response = requests.get(noaa_url)
    noaa_data = noaa_response.json()
    noaa_data_list = []
    for alert in noaa_data.get('features', []):
        noaa_data_list.append({
            'event_id': alert['id'],
            'type': alert['properties']['event'],
            'severity': alert['properties']['severity'],
            'area_affected': alert['properties']['areaDesc'],
            'start_time': alert['properties']['effective'],
            'end_time': alert['properties']['expires'],
        })
    return noaa_data_list

@router.get("/noaa-alerts", response_model=List[dict])
def noaa_alerts_route():
    return get_noaa_alerts()