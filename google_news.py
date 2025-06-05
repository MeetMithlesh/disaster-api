from fastapi import APIRouter
from typing import List
import requests
from bs4 import BeautifulSoup

router = APIRouter()

def get_google_news():
    url = "https://news.google.com/rss/search?q=natural+disasters&hl=en-US&gl=US&ceid=US:en"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch: {response.status_code}")
            return []
        soup = BeautifulSoup(response.content, "xml")
        news_items = soup.find_all("item")
        disaster_news = []
        for item in news_items:
            title = item.title.text
            link = item.link.text
            pub_date = item.pubDate.text
            disaster_news.append({"title": title, "link": link, "published_date": pub_date})
        return disaster_news
    except Exception as e:
        print(f"Error fetching Google News: {e}")
        return []

@router.get("/google-news", response_model=List[dict])
def google_news_route():
    return get_google_news()
