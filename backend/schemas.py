from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TopicCreate(BaseModel):
    topic_name: str

class Topic(BaseModel):
    topic_id: int
    topic_name: str
    article_count: int
    video_count: int

    class Config:
        from_attributes = True
        
class InferenceResponse(BaseModel):
    topic_id: int
    topic_name: str
    predicted_virality_score: float

class NewsReliabilitySource(BaseModel):
    source_id: int
    source_name: str
    publication_date: Optional[datetime]
    rank: int
    speed_score: int

class AnalyzeResponse(BaseModel):
    status: str
    topic_id: int
    message: str