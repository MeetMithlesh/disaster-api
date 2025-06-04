from fastapi import APIRouter, Query
from typing import Dict
import requests

router = APIRouter()

API_KEY = "fe1ab27d02217c92a0b0d60ebfb09c02"  # <-- Your OpenWeatherMap API key

def get_openweathermap_data(city: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    return response.json()

def extract_weather_details(data):
    if "main" in data and "weather" in data and "wind" in data:
        return {
            "city": data.get("name", "N/A"),
            "temperature_c": data["main"].get("temp", "N/A"),
            "feels_like_c": data["main"].get("feels_like", "N/A"),
            "humidity": data["main"].get("humidity", "N/A"),
            "pressure": data["main"].get("pressure", "N/A"),
            "weather_condition": data["weather"][0].get("description", "N/A") if data["weather"] else "N/A",
            "wind_speed": data["wind"].get("speed", "N/A"),
            "wind_direction": data["wind"].get("deg", "N/A"),
        }
    else:
        return {"error": "Invalid response from API"}

@router.get("/weather", response_model=Dict)
def weather_route(city: str = Query(...)):
    data = get_openweathermap_data(city)
    return extract_weather_details(data)