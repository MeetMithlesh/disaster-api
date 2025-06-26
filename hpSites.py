from fastapi import APIRouter
import json

router = APIRouter()

@router.get("/hp-sites")
async def read_hp_sites():
    with open("hpSites.json", "r") as f:
        data = json.load(f)
    return data

@router.get("/corebridge-sites")
async def read_corebridge_sites():
    with open("coreBridgeSites.json", "r") as f:
        data = json.load(f)
    return data
