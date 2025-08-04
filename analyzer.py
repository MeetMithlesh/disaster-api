from fastapi import APIRouter
from typing import List
from datetime import datetime
import feedparser
import json
import re
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

router = APIRouter()

class DisasterNewsAnalyzer:
    def __init__(self):
        self.rss_feeds = [
            "https://www.gdacs.org/xml/rss.xml",
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "http://feeds.bbci.co.uk/news/technology/rss.xml",
            # "https://www.bbc.com/news/world",
            # "https://www.afp.com/en/news-hub/1312/feed",
            # "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
            # "https://www.reuters.com/world/",
            "https://www.abplive.com/news/india/feed"
            "https://www.aljazeera.com/xml/rss/all.xml",
            "https://www.aljazeera.com/xml/rss/feeds/all.xml",
            # "https://rss.app/feeds/v1.1/5g6K8VAKCz1BFT2l.json",
        ]

        self.natural_disaster_keywords = {
            'earthquake': ['earthquake', 'quake', 'tremor', 'seismic'],
            'flood': ['flood', 'flooding', 'deluge', 'inundation', 'submerged'],
            'hurricane': ['hurricane', 'typhoon', 'cyclone', 'storm surge'],
            'wildfire': ['wildfire', 'forest fire', 'bush fire', 'burning'],
            'tornado': ['tornado', 'twister', 'windstorm'],
            'drought': ['drought', 'water shortage', 'water crisis'],
            'landslide': ['landslide', 'mudslide', 'rockfall']
        }

        self.manmade_disaster_keywords = {
            'explosion': ['explosion', 'blast', 'detonation', 'exploded'],
            'fire': ['fire', 'blaze', 'flames', 'burning building'],
            'chemical': ['chemical spill', 'toxic leak', 'contamination'],
            'transport': ['crash', 'collision', 'derailment', 'accident'],
            'infrastructure': ['bridge collapse', 'building collapse', 'structural failure'],
            'oil_spill': ['oil spill', 'oil leak', 'petroleum disaster']
        }

        self.emergency_terms = [
            'emergency', 'evacuation', 'evacuate', 'disaster',
            'rescue', 'warning', 'alert', 'danger', 'devastating',
            'catastrophe', 'crisis', 'casualties', 'damage', 'destroyed', 'shooting', 'crash', 'gaza', 'theft', 'robbery'
        ]

    def clean_text(self, text):
        text = BeautifulSoup(text, 'html.parser').get_text()
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        return text

    def analyze_text(self, text):
        cleaned_text = self.clean_text(text)
        result = {
            'is_disaster': False,
            'disaster_type': None,
            'disaster_category': None,
            'confidence': 0
        }

        for disaster_type, keywords in self.natural_disaster_keywords.items():
            if any(keyword in cleaned_text for keyword in keywords):
                result['is_disaster'] = True
                result['disaster_type'] = disaster_type 
                result['disaster_category'] = 'natural'
                result['confidence'] = self._calculate_confidence(cleaned_text, keywords)
                break

        if not result['is_disaster']:
            for disaster_type, keywords in self.manmade_disaster_keywords.items():
                if any(keyword in cleaned_text for keyword in keywords):
                    result['is_disaster'] = True
                    result['disaster_type'] = disaster_type
                    result['disaster_category'] = 'manmade'
                    result['confidence'] = self._calculate_confidence(cleaned_text, keywords)
                    break

        return result

    def _calculate_confidence(self, text, disaster_keywords):
        confidence = 0.5
        keyword_matches = sum(1 for keyword in disaster_keywords if keyword in text)
        confidence += 0.1 * keyword_matches
        emergency_matches = sum(1 for term in self.emergency_terms if term in text)
        confidence += 0.05 * emergency_matches
        return min(confidence, 1.0)

    def get_disaster_news(self):
        results = []
        
        # Original RSS feeds processing
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    full_text = f"{entry.get('title', '')} {entry.get('description', '')}"
                    analysis = self.analyze_text(full_text)

                    # Extract latitude and longitude if present
                    latitude = None
                    longitude = None

                    if 'geo_lat' in entry and 'geo_long' in entry:
                        latitude = entry.get('geo_lat')
                        longitude = entry.get('geo_long')
                    elif 'georss_point' in entry:
                        try:
                            georss_point = entry.get('georss_point')
                            if georss_point and isinstance(georss_point, str):
                                latlon = georss_point.split()
                                if len(latlon) >= 2:
                                    latitude = latlon[0]
                                    longitude = latlon[1]
                        except Exception:
                            pass
                    elif 'geometry' in entry:
                        try:
                            geometry = entry.get('geometry')
                            if isinstance(geometry, dict):
                                coords = geometry.get('coordinates')
                                if coords and isinstance(coords, (list, tuple)) and len(coords) >= 2:
                                    longitude = coords[0]
                                    latitude = coords[1]
                        except Exception:
                            pass

                    if analysis['is_disaster']:
                        if(analysis["disaster_type"] == "drought"):
                            continue
                        result = {
                            'title': entry.get('title', ''),
                            'description': entry.get('description', ''),
                            'link': entry.get('link', ''),
                            'timestamp': entry.get('published', ''),
                            'source': feed_url,
                            'latitude': latitude,
                            'longitude': longitude,
                            'analysis': analysis
                        }
                        results.append(result)
            except Exception as e:
                continue

        # Canadian Public Safety API
        try:
            current_date = datetime.now()
            week_ago = current_date - timedelta(days=7)
            date_filter = week_ago.strftime("%Y-%m-%d")
            
            canada_url = f"https://api.io.canada.ca/io-server/gc/news/en/v2?dept=publicsafetycanada&sort=publishedDate&orderBy=desc&publishedDate>={date_filter}&pick=50&format=atom"
            canada_feed = feedparser.parse(canada_url)
            
            for entry in canada_feed.entries:
                full_text = f"{entry.get('title', '')} {entry.get('description', '')}"
                analysis = self.analyze_text(full_text)
                
                if analysis['is_disaster']:
                    results.append({
                        'title': entry.get('title', ''),
                        'description': entry.get('description', ''),
                        'link': entry.get('link', ''),
                        'timestamp': entry.get('published', ''),
                        'source': "Public Safety Canada",
                        'latitude': None,
                        'longitude': None,
                        'analysis': analysis
                    })
        except Exception as e:
            print(f"Error fetching Canadian Public Safety data: {e}")

        # Environment and Climate Change Canada Weather Alerts
        try:
            eccc_url = "https://weather.gc.ca/data/dms/alert_geojson_v2/alerts.public.en.geojson"
            eccc_response = requests.get(eccc_url)
            eccc_data = eccc_response.json()
            
            for feature in eccc_data.get('features', []):
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                
                # Extract coordinates if available
                coordinates = geometry.get('coordinates')
                latitude = None
                longitude = None
                
                if coordinates:
                    if geometry.get('type') == 'Point':
                        longitude, latitude = coordinates[0], coordinates[1]
                    # elif geometry.get('type') in ['Polygon', 'MultiPolygon']:
                    #     # For polygons, use centroid or first coordinate as representative
                    #     if geometry.get('type') == 'Polygon' and coordinates[0]:
                    #         longitude, latitude = coordinates[0][0][0], coordinates[0][0][1]
                    #     elif geometry.get('type') == 'MultiPolygon' and coordinates[0][0]:
                    #         longitude, latitude = coordinates[0][0][0][0], coordinates[0][0][0][1]
                
                # Determine disaster type from alert type
                alert_type = properties.get('type', '').lower()
                disaster_type = 'severe weather'
                if 'flood' in alert_type:
                    disaster_type = 'flood'
                elif 'storm' in alert_type or 'wind' in alert_type:
                    disaster_type = 'hurricane'
                elif 'fire' in alert_type:
                    disaster_type = 'wildfire'
                elif 'tornado' in alert_type:
                    disaster_type = 'tornado'
                
                results.append({
                    'title': properties.get('alertName', ''),
                    'description': properties.get('text', ''),
                    'link': properties.get('web', 'https://weather.gc.ca/'),
                    'timestamp': properties.get('sent', ''),
                    'source': "Environment and Climate Change Canada",
                    'latitude': latitude,
                    'longitude': longitude,
                    'analysis': {
                        'is_disaster': True,
                        'disaster_type': disaster_type,
                        'disaster_category': 'natural',
                        'confidence': 0
                    }
                })
        except Exception as e:
            print(f"Error fetching ECCC data: {e}")

        # NASA Earth Observatory Natural Disasters
        try:
            nasa_url = "https://earthobservatory.nasa.gov/feeds/natural-hazards.rss"
            nasa_feed = feedparser.parse(nasa_url)
            
            for entry in nasa_feed.entries:
                results.append({
                    'title': entry.get('title', ''),
                    'description': entry.get('description', ''),
                    'link': entry.get('link', ''),
                    'timestamp': entry.get('published', ''),
                    'source': "NASA Earth Observatory",
                    'latitude': None,
                    'longitude': None,
                    'analysis': {
                        'is_disaster': True,
                        'disaster_type': 'various',
                        'disaster_category': 'natural',
                        'confidence': 1.0
                    }
                })
        except Exception as e:
            print(f"Error fetching NASA data: {e}")

        # Australian Earthquake Data
        try:
            ega_url = "https://earthquakes.ga.gov.au/geoserver/earthquakes/wfs?service=WFS&request=getfeature&typeNames=earthquakes:earthquakes_seven_days&outputFormat=application/json&CQL_FILTER=display_flag=%27Y%27"
            ega_response = requests.get(ega_url)
            ega_data = ega_response.json()

            for event in ega_data['features']:
                mag = event['properties']['mb']
                # print(f"{type(mag)} type of mag")
                if type(mag) != float:
                    continue
                else:
                    if( mag < 3.5):
                     continue
                results.append({
                    'title': "Earthquake Alert",
                    'description': f'Earthquake in {event["properties"]["description"]} with magnitude {event["properties"]["mb"]} and depth {event["properties"]["depth"]} km.',
                    'link': "https://earthquakes.ga.gov.au/",
                    'timestamp': event['properties']['epicentral_time'],
                    'source': 'EGA',
                    'latitude': event['geometry']['coordinates'][1],
                    'longitude': event['geometry']['coordinates'][0],
                    'analysis': {
                        'is_disaster': True,
                        'disaster_type': 'earthquake',
                        'disaster_category': 'natural',
                        'confidence': 0.5
                    }
                })
        except Exception as e:
            print(f"Error fetching EGA data: {e}")

        # Australian Hazard Watch
        try:
            h_watch_url = "https://www.hazardwatch.gov.au/app-api/alerts"
            h_watch_response = requests.get(h_watch_url)
            h_watch_data = h_watch_response.json()
            
            for alert in h_watch_data.get('alerts', []):
                id = alert.get('identifier')        
                coordinates = None
                for feature in h_watch_data.get('geojson', {}).get('features', []):
                    if feature.get('properties', {}).get('alertIdentifier') == id:
                        geometries = feature.get('geometry', {}).get('geometries', [])
                        for geom in geometries:
                            if geom.get('type') == 'Point':
                                coordinates = geom.get('coordinates')
                                break
                        # if coordinates is None:
                        #     for geom in geometries:
                        #         if geom.get('type') == 'Polygon':
                        #             coordinates = geom.get('coordinates')
                        #             break
                        break
                        
                results.append({
                    'title': alert.get('info').get('headline').strip(),
                    'description': f"{alert.get('info').get('event')} in {alert.get('info').get('parameter').get('AffectedLocation')}",
                    'link': "https://www.hazardwatch.gov.au/",
                    'timestamp': alert.get('sent'),
                    'source': alert.get('info').get('web'),
                    'latitude': coordinates[0] if coordinates else None,
                    'longitude': coordinates[1] if coordinates else None,
                    'analysis': {
                        "is_disaster": True, 
                        "disaster_type": alert.get('info').get('event'),
                        "disaster_category": "natural",
                        "confidence": 0.8,
                    }
                })
        except Exception as e:
            print(f"Error fetching Hazard Watch data: {e}")

        # Japan Meteorological Agency
        try:
            jma_url = "https://www.jma.go.jp/bosai/information/data/information.json"
            jma_response = requests.get(jma_url)
            jma_data = jma_response.json()

            for event in jma_data:
                results.append({
                    'title': event.get('headTitle'),
                    'description': f"{event.get('controlTitle')} by {event.get('publishingOffice')}",
                    'link': "https://www.jma.go.jp/jma/index.html",
                    'timestamp': event.get('reportDatetime'),
                    'source': "Japan Meteorological Agency (JMA)",
                    'latitude': None, 
                    'longitude': None,  
                    'analysis': {
                        "is_disaster": True,
                        "disaster_type": event.get('infoType'),
                        "disaster_category": "natural",
                        "confidence": 0.8
                    }
                })
        except Exception as e:
            print(f"Error fetching JMA data: {e}")

        # Emergency WA
        try:
            ewg_url = "https://api.emergency.wa.gov.au/v1/warnings"
            ewg_response = requests.get(ewg_url)
            ewg_data = ewg_response.json()

            for event in ewg_data.get('warnings', []):
                results.append({
                    'title': event.get('title'),
                    'description': event.get('title'),
                    'link': "https://www.emergency.wa.gov.au/",
                    'timestamp': event.get('published-date-time'),
                    'source': "Emergency WA",
                    'latitude': event.get('location', {}).get('latitude'),
                    'longitude': event.get('location', {}).get('longitude'),
                    'analysis': {
                        'is_disaster': True,
                        'disaster_type': event.get('type'),
                        'disaster_category': 'natural',
                        'confidence': 1.0
                    }
                })
        except Exception as e:
            print(f"Error fetching Emergency WA data: {e}")

        # WMO Severe Weather
        try:
            url = "https://severeweather.wmo.int/json/wmo_all.json?_=1749709078759"
            response = requests.get(url)
            data = response.json()
            
            for items in data.get("items", []):
                if items.get('areaDesc') == "":
                    continue
                results.append({
                    "title": items.get("headline"),
                    "description": f"{items.get('event')} in {items.get('areaDesc')} and expires at {items.get('expires')}",
                    "link": "https://severeweather.wmo.int/",
                    "timestamp": items.get("sent"),
                    "source": "WMO Severe Weather",
                    "latitude": None,
                    "longitude": None,
                    "analysis": {
                        'is_disaster': True,
                        'disaster_type': 'severe weather',
                        'disaster_category': 'natural',
                        'confidence': 0
                    }
                })
        except Exception as e:
            print(f"Error fetching WMO data: {e}")

        # # USGS Earthquakes - Enhanced with limit parameter
        # try:
        #     URL = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100&starttime=" + (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d') + "&endtime=" + datetime.now().strftime('%Y-%m-%d')
        #     usgs = requests.get(URL)
        #     data = usgs.json()
            
        #     for feature in data["features"]:
        #         properties = feature["properties"]
        #         geometry = feature["geometry"]
        #         timestamp = properties["time"]
        #         datetime_obj = pd.to_datetime(timestamp, unit="ms")
        #         results.append({
        #             "title": properties["title"],
        #             "description": f"Earthquake at {properties.get('place')}",
        #             "link": properties["url"],
        #             "timestamp": datetime_obj.isoformat(),
        #             "source": "USGS",
        #             "latitude": geometry["coordinates"][1],
        #             "longitude": geometry["coordinates"][0],
        #             "analysis": {
        #                 'is_disaster': True,
        #                 'disaster_type': 'earthquake',
        #                 'disaster_category': 'natural',
        #                 'confidence': 1
        #             }
        #         })
        # except Exception as e:
        #     print(f"Error fetching USGS data: {e}")

        # USGS All Day Earthquakes (additional feed)
        try:
            URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
            usgs = requests.get(URL)
            data = usgs.json()
            
            for feature in data["features"]:
                properties = feature["properties"]
                geometry = feature["geometry"]
                timestamp = properties["time"]
                datetime_obj = pd.to_datetime(timestamp, unit="ms")
                # if(properties["mag"] < 3.5):
                #     continue
                results.append({
                    "title": properties["title"],
                    "description": f"Earthquake at {properties.get('place')}",
                    "link": properties["url"],
                    "timestamp": datetime_obj.isoformat(),
                    "source": "USGS All Day",
                    "latitude": geometry["coordinates"][1],
                    "longitude": geometry["coordinates"][0],
                    "analysis": {
                        'is_disaster': True,
                        'disaster_type': 'earthquake',
                        'disaster_category': 'natural',
                        'confidence': 1
                    }
                })
        except Exception as e:
            print(f"Error fetching USGS All Day data: {e}")
        # NOAA Weather Alerts (US)
        try:
            noaa_url = "https://api.weather.gov/alerts/active"
            noaa_response = requests.get(noaa_url)
            noaa_data = noaa_response.json()
            
            for alert in noaa_data.get('features', []):
                properties = alert.get('properties', {})
                geometry = alert.get('geometry')
                
                # Extract coordinates if available
                latitude = None
                longitude = None
                if geometry and geometry.get('coordinates'):
                    coords = geometry.get('coordinates')
                    if geometry.get('type') == 'Point':
                        longitude, latitude = coords[0], coords[1]
                    elif geometry.get('type') == 'Polygon' and coords:
                        # For polygons, use the first coordinate pair as representative
                        if coords[0] and len(coords[0]) > 0:
                            longitude, latitude = coords[0][0][0], coords[0][0][1]
                
                # Determine disaster type based on event
                event_type = properties.get('event', '').lower()
                disaster_type = 'severe weather'
                if 'tornado' in event_type:
                    disaster_type = 'tornado'
                elif 'flood' in event_type:
                    disaster_type = 'flood'
                elif 'hurricane' in event_type or 'typhoon' in event_type:
                    disaster_type = 'hurricane'
                elif 'fire' in event_type:
                    disaster_type = 'wildfire'
                elif 'earthquake' in event_type:
                    disaster_type = 'earthquake'
                
                results.append({
                    'title': properties.get('headline', ''),
                    'description': properties.get('description', ''),
                    'link': properties.get('web', 'https://www.weather.gov/'),
                    'timestamp': properties.get('sent', ''),
                    'source': "NOAA Weather Service",
                    'latitude': latitude,
                    'longitude': longitude,
                    'analysis': {
                        'is_disaster': True,
                        'disaster_type': disaster_type,
                        'disaster_category': 'natural',
                        'confidence': 1.0
                    }
                })
        except Exception as e:
            print(f"Error fetching NOAA alerts data: {e}")

        # UN OCHA ReliefWeb Disasters
        try:
            # Get disasters from the last 30 days
            reliefweb_url = "https://api.reliefweb.int/v1/disasters"
            params = {
                'appname': 'disaster-monitor',
                'limit': 50,
                'fields[include]': ['name', 'description', 'url', 'date', 'primary_country', 'primary_type', 'status'],
                'filter[field]': 'date.created',
                'filter[value][from]': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'filter[value][to]': datetime.now().strftime('%Y-%m-%d')
            }
            
            reliefweb_response = requests.get(reliefweb_url, params=params)
            reliefweb_data = reliefweb_response.json()
            
            for disaster in reliefweb_data.get('data', []):
                fields = disaster.get('fields', {})
                
                # Map ReliefWeb disaster types to our categories
                primary_type = fields.get('primary_type', {}).get('name', '').lower()
                disaster_type = 'disaster'
                disaster_category = 'natural'
                
                if 'earthquake' in primary_type:
                    disaster_type = 'earthquake'
                elif 'flood' in primary_type:
                    disaster_type = 'flood'
                elif 'storm' in primary_type or 'cyclone' in primary_type or 'hurricane' in primary_type:
                    disaster_type = 'hurricane'
                elif 'fire' in primary_type:
                    disaster_type = 'wildfire'
                elif 'drought' in primary_type:
                    disaster_type = 'drought'
                elif 'landslide' in primary_type:
                    disaster_type = 'landslide'
                elif 'explosion' in primary_type or 'industrial' in primary_type:
                    disaster_type = 'explosion'
                    disaster_category = 'manmade'
                elif 'transport' in primary_type or 'accident' in primary_type:
                    disaster_type = 'transport'
                    disaster_category = 'manmade'
                
                # Get country info for location context
                country_name = fields.get('primary_country', {}).get('name', 'Unknown')
                
                results.append({
                    'title': fields.get('name', ''),
                    'description': f"{fields.get('description', '')} Location: {country_name}",
                    'link': fields.get('url', 'https://reliefweb.int/'),
                    'timestamp': fields.get('date', {}).get('created', ''),
                    'source': "UN OCHA ReliefWeb",
                    'latitude': None,
                    'longitude': None,
                    'analysis': {
                        'is_disaster': True,
                        'disaster_type': disaster_type,
                        'disaster_category': disaster_category,
                        'confidence': 0
                    }
                })
        except Exception as e:
            print(f"Error fetching ReliefWeb data: {e}")

        try:
            url = "https://zoom.earth/data/storms/?date=" + (datetime.now() - timedelta(days=0)).strftime('%Y-%m-%d')
            # print(url)
            detail_url = "https://zoom.earth/data/storms/?id="
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }

            zoom_response = requests.get(url, headers=headers)

            if zoom_response.status_code == 200:
                zoom_data = zoom_response.json()
            else:
                print(f"Failed to retrieve data. Status code: {zoom_response.status_code}")

            storm_id = [storm for storm in zoom_data['storms']]

            # print(f"Storm IDs: {storm_id}")

            for storm in storm_id:
                trail = []
                # print(f"Processing storm ID: {storm}")
                zoom_storm_data = requests.get(detail_url + storm, headers=headers).json()
                track_count = 0
                latitude = None
                longitude = None
                for track in zoom_storm_data.get("track", []):
                    track_count = track_count+1
                    coordinates = track.get("coordinates", [])
                    latitude = coordinates[1] if coordinates else None
                    longitude = coordinates[0] if coordinates else None
                    trail.append({
                        "latitude": latitude,
                        "longitude": longitude,
                        "timestamp": track.get("date", None),
                        "description": track.get("description", None),
                        "code": track.get("code", None)
                            })

                zoom_timestamp = zoom_storm_data.get("track")[track_count-1].get("date", None)

                results.append({
                    "title": zoom_storm_data.get("title", "Storm"),
                    "description": f"{zoom_storm_data.get("description", "")} {zoom_storm_data.get("place", "unknown")}",
                    "link": "https://zoom.earth",
                    "timestamp": zoom_timestamp,
                    "source": "Zoom Earth",
                    "latitude": latitude,
                    "longitude": longitude,
                    "analysis": {
                        "is_disaster": True,
                        "disaster_type": zoom_storm_data.get("type", "unknown"),
                        "disaster_category": "natural",
                        "confidence": 0.5
                    },
                    "trail": trail
                })


        except Exception as e:
            print(f"Error fetching zoom earth data: {e}")

        # RDI Power Platform Incidents
        try:
            rdi_url = "https://rdipowerplatformfd-e5hhgqaahef7fbdr.a02.azurefd.net/incidents/incidents.json"
            rdi_response = requests.get(rdi_url)
            rdi_response.raise_for_status()
            incidents = rdi_response.json()
    
            for incident in incidents:
                attributes = incident.get("attributes", {})
    
                # Required fields
                title = attributes.get("name", "Incident Report")
                description = attributes.get("conditionStatement", "")
                incident_type = "wildfire" if attributes.get("calFireIncident", False) else "incident"
                disaster_category = "natural" if incident_type == "wildfire" else "manmade"
    
                # Location
                latitude = attributes.get("latitude")
                longitude = attributes.get("longitude")
                location = attributes.get("location", "")
    
                # Timestamp
                timestamp = attributes.get("started", datetime.utcnow().isoformat())
    
                # Link to the incident
                base_url = "https://rdipowerplatformfd-e5hhgqaahef7fbdr.a02.azurefd.net"
                link = base_url + attributes.get("url", "/")
    
                results.append({
                    "title": title,
                    "description": description,
                    "link": "https://www.fire.ca.gov/",
                    "timestamp": timestamp,
                    "source": "RDI Power Platform",
                    "latitude": latitude,
                    "longitude": longitude,
                    "analysis": {
                        "is_disaster": True,
                        "disaster_type": "Natural",
                        "disaster_category": "Natural",
                        "confidence": 0.9
                    }
                })
        except Exception as e:
            print(f"Error fetching RDI Power Platform data: {e}")
        try:
            url = "https://sachet.ndma.gov.in/cap_public_website/FetchAllAlertDetails"
            response = requests.get(url)
            data = response.json()

            for alert in data:
                # Extract latitude and longitude from 'centroid'
                centroid = alert.get("centroid", "")
                latitude, longitude = None, None
                if centroid and "," in centroid:
                    lon_str, lat_str = centroid.strip().split(",")
                    latitude = float(lat_str.strip())
                    longitude = float(lon_str.strip())

                results.append( {
                    "title": alert["disaster_type"] + " Alert",
                    "description": alert["warning_message"],
                    "link": "sachet.ndma.gov.in",  # No link provided by API
                    "timestamp": alert["effective_start_time"],
                    "source": alert["alert_source"],
                    "latitude": latitude,
                    "longitude": longitude,
                    # "location": alert.get("area_description"),  # No list manipulation
                    "analysis": {
                        "is_disaster": True,
                        # "disaster_type": alert["disaster_type"], 
                        "disaster_type": "Weather", 
                        "disaster_category": "natural",
                        "confidence": 0.9
                    }
                })

        except Exception as e:
            print(f"Error fetching NDMA data: {e}")

        # try:     
        #     url = "https://weather.gc.ca/data/dms/alert_geojson_v2/alerts.public.en.geojson"
        #     response = requests.get(url)
        #     data = response.json()
        #     alerts = data.get("alerts", {})

        #     for alert_key, alert in alerts.items():
        #         # Try to extract first available URL from special_text if available
        #         link = None
        #         special_text = alert.get("special_text", [])
        #         for item in special_text:
        #             if item.get("type") == "URL":
        #                 link = item.get("link")
        #                 break
                    
        #         results.append( {
        #             "title": alert.get("alertName", alert.get("alertNameShort", "Alert")),
        #             "description": alert.get("text", ""),
        #             "link": link,
        #             "timestamp": alert.get("issueTime"),
        #             "source": "Environment Canada",
        #             "latitude": None,   # No coordinates provided in this API
        #             "longitude": None,  # No coordinates provided in this API
        #             # "location": alert.get("alertHeaderText", "Canada"),  # Fallback to alertHeaderText
        #             "analysis": {
        #                 "is_disaster": True,
        #                 "disaster_type": alert.get("alertNameShort", "unknown"),
        #                 "disaster_category": "natural",
        #                 "confidence": 0
        #             }
        #         })
        # except Exception as e:
        #     print(f"Error fetching Environment Canada data: {e}")


        # URL to fetch the active warnings
        url = "https://www.tornadohq.com/json/active_warnings.json?_=1750227202352"
        # Fetch the data
        response = requests.get(url)
        data = response.json()

        for item in data:
            points = item.get("points", [])
            if points and isinstance(points[0], list) and len(points[0]) >= 2:
                  latitude, longitude = points[0][0], points[0][1]
            else:
                latitude, longitude = None, None


            # Extract location from full_text
            match = re.search(r"Locations impacted include\.\.\.(.*?)(?:\n\n|PRECAUTIONARY)", item.get("full_text", ""), re.DOTALL | re.IGNORECASE)
            locations = match.group(1).strip().replace('\n', ', ') if match else None

            # Construct URL based on ID
            # warning_id = item.get("id")
            # link = f"https://alerts.weather.gov/cap/{warning_id}.html" if warning_id else None

            results.append( {
                "title": f"{item.get('phenomena', '').capitalize()} Warning",
                "description": item.get("headline"),
                "link": "https://www.tornadohq.com",
                "timestamp": item.get("event_start"),
                "source": "National Weather Service",
                "latitude": latitude,
                "longitude": longitude,
                "analysis": {
                    "is_disaster": True,
                    "disaster_type": item.get("phenomena", "unknown"),
                    "disaster_category": "natural",
                    "confidence": 0.9
                }
            })
    
        try:
            google_rss_url = "https://rss.app/feeds/v1.1/5g6K8VAKCz1BFT2l.json"
            response = requests.get(google_rss_url)
            response.raise_for_status()
            data = response.json()

            # Handle JSON Feed format
            items = data.get('items', [])
            for item in items:
                # Combine title and content for analysis
                title = item.get('title', '')
                content = item.get('content_text', '') or item.get('content_html', '')

                # Clean HTML content if present
                if item.get('content_html') and not item.get('content_text'):
                    content = BeautifulSoup(item.get('content_html'), 'html.parser').get_text()

                full_text = f"{title} {content}"
                analysis = self.analyze_text(full_text)

                if analysis['is_disaster']:
                    if analysis["disaster_type"] == "drought":
                        continue

                    # Get author name if available
                    authors = item.get('authors', [])
                    author_name = authors[0].get('name') if authors else "Unknown"

                    result = {
                        'title': title,
                        'description': content[:500] + "..." if len(content) > 500 else content,  # Truncate long descriptions
                        'link': item.get('url', ''),
                        'timestamp': item.get('date_published', ''),
                        'source': f"Google News ({author_name})",
                        'latitude': None,
                        'longitude': None,
                        'analysis': analysis
                    }
                    results.append(result)
            # return results
                
        except requests.RequestException as e:
            print(f"Error fetching Google RSS data - Network error: {e}")
        except KeyError as e:
            print(f"Error parsing Google RSS data - Missing key: {e}")
        except Exception as e:
            print(f"Error fetching Google RSS data: {e}")

        try:
            url = "https://www.click2houston.com/arc/outboundfeeds/rss/category/news/local/?outputType=xml&size=10"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
    
            root = ET.fromstring(response.content)
            channel = root.find("channel")
            if channel is None:
                print(f"Error: <channel> tag not found in Click2Houston feed.")
                return
            items = channel.findall("item")
    
            news_list = []
    
            for item in items:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                pub_date = item.findtext("pubDate", "").strip()
                description_raw = item.findtext("description", "")
                description = clean_html(description_raw)
    
                # Try parsing the date
                try:
                    timestamp = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z").isoformat()
                except:
                    timestamp = None
    
                news = {
                    "title": title,
                    "description": description,
                    "link": link,
                    "timestamp": timestamp,
                    "source": "Click2Houston",
                    "latitude": None,
                    "longitude": None,
                    # "location": None,
                    "analysis": {
                        "is_disaster": False,
                        "disaster_type": "manmade",
                        "disaster_category": None,
                        "confidence": 0
                    }
                }
    
                results.append(news)
        except Exception as e:
            print(f"Error fetching Click2Houston data: {e}")

        try:
            fox_news = fetch_fox_news_feed(FOX_NEWS_RSS_FEEDS)
            if fox_news:
                results.extend(fox_news)
            # return results
        except Exception as e:
            print(f"Error fetching Fox News data: {e}")

        try:
            xinhua_news = extract_from_xinhua_feed(XINHUA_RSS_FEEDS)
            if xinhua_news:
                results.extend(xinhua_news)
            return results
        except Exception as e:
            print(f"Error fetching Xinhua News data: {e}")
            return results


@router.get("/disaster-news", response_model=List[dict])   
def retrieve_disaster_news():
    analyzer = DisasterNewsAnalyzer()
    return analyzer.get_disaster_news() 
     
# Xinhua News RSS Feeds
XINHUA_RSS_FEEDS = [
    "http://www.xinhuanet.com/english/rss/worldrss.xml",
    "http://www.xinhuanet.com/english/rss/chinarss.xml",
    "http://www.xinhuanet.com/english/rss/businessrss.xml",
    "http://www.xinhuanet.com/english/rss/travelrss.xml",
    "http://www.xinhuanet.com/english/rss/sportsrss.xml",
    "http://www.xinhuanet.com/english/rss/scirss.xml",
    "http://www.xinhuanet.com/english/rss/entertainmentrss.xml",
    "http://www.xinhuanet.com/english/rss/healthrss.xml",
    "http://www.xinhuanet.com/english/rss/travelrss.xml",
    "http://www.xinhuanet.com/english/rss/newchina.xml",
    "http://www.xinhuanet.com/english/rss/indepthrss.xml",
    "http://www.xinhuanet.com/english/rss/newchina.xml",
    # Add more if needed
]

FOX_NEWS_RSS_FEEDS = [
    "https://moxie.foxnews.com/google-publisher/latest.xml",
    "https://moxie.foxnews.com/google-publisher/opinion.xml",
    "https://moxie.foxnews.com/google-publisher/us.xml",
    "https://moxie.foxnews.com/google-publisher/world.xml",
    "https://moxie.foxnews.com/google-publisher/politics.xml",
    "https://moxie.foxnews.com/google-publisher/health.xml",
    "https://moxie.foxnews.com/google-publisher/science.xml",
    "https://moxie.foxnews.com/google-publisher/tech.xml",
    "https://moxie.foxnews.com/google-publisher/sports.xml",
]

def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=" ").strip()
def parse_xinhua_news_rss_feed(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        channel = root.find("channel")
        if channel is None:
            print(f"Error: <channel> tag not found in feed {url}")
            return []
        items = channel.findall("item")
        parsed_items = []
        for item in items:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            raw_description = item.findtext("description", "")
            description = clean_html(raw_description)
            # Format the date
            try:
                timestamp = datetime.strptime(pub_date, "%Y-%m-%d").isoformat() + "Z"
            except:
                timestamp = None
            data = {
                "title": title,
                "description": description,
                "link": link,
                "timestamp": timestamp,
                "source": "Xinhua News",
                "latitude": None,
                "longitude": None,
                # "location": None,
                "analysis": {
                    "is_disaster": False,
                    "disaster_type": "manmade",
                    "disaster_category": None,
                    "confidence": 0
                }
            }
            parsed_items.append(data)
        return parsed_items
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []
def extract_from_xinhua_feed(feed_urls):
    all_results = []
    for url in feed_urls:
        feed_data = parse_xinhua_news_rss_feed(url)
        all_results.extend(feed_data)
    return all_results

def parse_fox_news_rss_feed(url, source="Fox News"):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        channel = root.find("channel")
        if channel is None:
            print(f"Error: <channel> tag not found in feed {url}")
            return []
        items = channel.findall("item")

        articles = []
        for item in items:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            raw_description = item.findtext("description", "").strip()
            description = clean_html(raw_description)

            pub_date_raw = item.findtext("pubDate", "").strip()
            try:
                pub_date = datetime.strptime(pub_date_raw, "%a, %d %b %Y %H:%M:%S %z").isoformat()
            except Exception:
                pub_date = None

            article = {
                "title": title,
                "description": description,
                "link": link,
                "timestamp": pub_date,
                "source": source,
                "latitude": None,
                "longitude": None,
                # "location": None,
                "analysis": {
                    "is_disaster": False,
                    "disaster_type": "manmade",
                    "disaster_category": None,
                    "confidence": 0
                }
            }
            articles.append(article)
        return articles

    except Exception as e:
        print(f"[ERROR] {url} — {e}")
        return []

def fetch_fox_news_feed(feed_urls):
    all_articles = []
    for url in feed_urls:
        articles = parse_fox_news_rss_feed(url)
        if articles is not None:
            all_articles.extend(articles)
    return all_articles


