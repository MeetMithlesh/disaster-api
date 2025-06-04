from pydantic import BaseModel
from typing import List, Optional

class DisasterNews(BaseModel):
    timestamp: str
    title: str
    description: str
    link: str
    published: str
    source: str
    analysis: dict

class DisasterNewsResponse(BaseModel):
    news: List[DisasterNews]
    count: int
    message: Optional[str] = None