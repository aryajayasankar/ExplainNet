from pydantic import BaseModel
from typing import Optional, List, Dict
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

class ChannelMetrics(BaseModel):
    channelName: str
    impactScore: float
    speedFactor: float
    frequencyFactor: float
    averageEngagement: float

class YouTubeMetrics(BaseModel):
    channels: List[ChannelMetrics]
    viewsData: List[Dict]
    sentimentAnalysis: List[Dict]

class GuardianMetrics(BaseModel):
    reliability: float
    coverage: float
    articles: int
    timelineData: List[Dict]

class NewsSourceRanking(BaseModel):
    sourceName: str
    reliabilityScore: float
    speedFactor: float
    consistencyFactor: float

class NewsMetrics(BaseModel):
    guardian: GuardianMetrics
    overall: Dict[str, List]

class TimelineData(BaseModel):
    dates: List[str]
    views: List[List[int]]
    channels: List[str]

class SentimentData(BaseModel):
    videoId: str
    sentimentScore: float
    engagementScore: float

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