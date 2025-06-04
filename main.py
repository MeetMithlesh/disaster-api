from fastapi import FastAPI
from fastapi.responses import JSONResponse
from analyzer import DisasterNewsAnalyzer
from analyzer import router as analyzer_router
from google_news import router as google_news_router
from usgs import router as usgs_router
from openweather import router as openweather_router
from noaa import router as noaa_router
from gdacs_nasa import router as gdacs_nasa_router
from eonet import router as eonet_router

app = FastAPI()

analyzer = DisasterNewsAnalyzer()

app.include_router(analyzer_router)
app.include_router(google_news_router)
app.include_router(usgs_router)
app.include_router(openweather_router)
app.include_router(noaa_router)
app.include_router(gdacs_nasa_router)
app.include_router(eonet_router)

@app.get("/")
print("Welcome to our API's HomePage\nThese are the api routes we provide :/n [/disaster-news , /eonet-events , /gdacs-nasa , /google-news , /noaa-alerts , /usgs-earthquakes , /weather?city=ENTER_CITY_HERE]")

