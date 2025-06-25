from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from analyzer import DisasterNewsAnalyzer
from analyzer import router as analyzer_router
from google_news import router as google_news_router
from usgs import router as usgs_router
from openweather import router as openweather_router
from noaa import router as noaa_router
from gdacs_nasa import router as gdacs_nasa_router
from eonet import router as eonet_router
from hpSites import router as hp_sites_router

app = FastAPI()


app = FastAPI()

origins = [
    "*",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyzer_router)
app.include_router(google_news_router)
app.include_router(usgs_router)
app.include_router(openweather_router)
app.include_router(noaa_router)
app.include_router(gdacs_nasa_router)
app.include_router(eonet_router)
app.include_router(hp_sites_router)

@app.get("/")
async def home():
    return JSONResponse(content={"message": "Welcome to the Disaster News API. Use the provided routes to access various disaster-related data.[/disaster-news , /eonet-events , /gdacs-nasa , /google-news , /noaa-alerts , /usgs-earthquakes , /weather?city=ENTER_CITY_HERE]"})
