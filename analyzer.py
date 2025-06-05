from fastapi import APIRouter
from typing import List
from datetime import datetime
import feedparser
import json
import re
from bs4 import BeautifulSoup

router = APIRouter()

class DisasterNewsAnalyzer:
    def __init__(self):
        self.rss_feeds = [
            "https://www.gdacs.org/xml/rss.xml",
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.atom",
            "https://www.meteoalarm.eu/documents/rss/ro.rss",
            "https://feeds.reliefweb.int/rss/disasters",
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "https://www.afp.com/en/news-hub/1312/feed",
            "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
            "https://www.reuters.com/world/",
            # "http://feeds.bbci.co.uk/news/technology/rss.xml",
            "https://www.bbc.com/news/world"
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

    # def get_disaster_news(self):
    #     results = []
    #     for feed_url in self.rss_feeds:
    #         try:
    #             feed = feedparser.parse(feed_url)
    #             for entry in feed.entries:
    #                 full_text = f"{entry.get('title', '')} {entry.get('description', '')}"
    #                 analysis = self.analyze_text(full_text)

    #                 if analysis['is_disaster']:
    #                     result = {
    #                         'timestamp': str(datetime.now()),
    #                         'title': entry.get('title', ''),
    #                         'description': entry.get('description', ''),
    #                         'link': entry.get('link', ''),
    #                         'published': entry.get('published', ''),
    #                         'source': feed_url,
    #                         'analysis': analysis
    #                     }
    #                     results.append(result)
    #         except Exception as e:
    #             continue
    #     return results
    def get_disaster_news(self):
        results = []
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    full_text = f"{entry.get('title', '')} {entry.get('description', '')}"
                    analysis = self.analyze_text(full_text)

                    # --- Extract latitude and longitude if present ---
                    latitude = None
                    longitude = None

                    # Common georss/geo fields
                    if 'geo_lat' in entry and 'geo_long' in entry:
                        latitude = entry.get('geo_lat')
                        longitude = entry.get('geo_long')
                    elif 'georss_point' in entry:
                        try:
                            latlon = entry.get('georss_point').split()
                            latitude = latlon[0]
                            longitude = latlon[1]
                        except Exception:
                            pass
                    # Sometimes coordinates are in 'geometry'
                    elif 'geometry' in entry and isinstance(entry['geometry'], dict):
                        coords = entry['geometry'].get('coordinates')
                        if coords and isinstance(coords, (list, tuple)) and len(coords) >= 2:
                            longitude = coords[0]
                            latitude = coords[1]

                    if analysis['is_disaster']:
                        result = {
                            # 'fetched_time': str(datetime.now()),
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
        return results

@router.get("/disaster-news", response_model=List[dict])
def retrieve_disaster_news():
    analyzer = DisasterNewsAnalyzer()
    return analyzer.get_disaster_news()
