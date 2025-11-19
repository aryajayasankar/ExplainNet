from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SentimentType(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"
    MIXED = "MIXED"


# Topic Schemas
class TopicCreate(BaseModel):
    topic_name: str = Field(..., min_length=1, max_length=500)


class TopicResponse(BaseModel):
    id: int
    topic_name: str
    created_at: datetime
    last_analyzed_at: Optional[datetime]
    analysis_status: AnalysisStatus
    total_videos: int
    total_articles: int
    videos_found: int = 0
    articles_found: int = 0
    overall_sentiment: Optional[SentimentType]
    overall_impact_score: Optional[float]
    error_message: Optional[str]
    unique_sources_count: int = 0

    class Config:
        from_attributes = True


# Video Schemas
class VideoResponse(BaseModel):
    id: int
    topic_id: int
    video_id: str
    title: str
    channel_name: str
    channel_id: str
    thumbnail_url: Optional[str]
    published_at: Optional[datetime]
    view_count: int
    like_count: int
    comment_count: int
    duration: Optional[str]
    impact_score: Optional[float]
    reach_score: Optional[float]
    engagement_score: Optional[float]
    sentiment_score: Optional[float]
    quality_score: Optional[float]
    influence_score: Optional[float]
    recency_boost: Optional[float]
    overall_sentiment: Optional[SentimentType]
    emotions_json: Optional[str] = None
    emotions: Optional[str] = None  # Alias for emotions_json for frontend compatibility

    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True


# Sentiment Schemas
class SentimentResponse(BaseModel):
    id: int
    video_id: int
    model_name: str
    sentiment: Optional[SentimentType]
    confidence: float
    positive_score: Optional[float]
    negative_score: Optional[float]
    neutral_score: Optional[float]
    # Justification and sarcasm (when provided by model)
    gemini_justification: Optional[str] = None
    gemini_sarcasm_score: Optional[float] = None
    hf_justification: Optional[str] = None

    class Config:
        from_attributes = True


# Comment Schemas
class CommentResponse(BaseModel):
    id: int
    video_id: int
    comment_id: str
    author: str
    text: str
    like_count: int
    published_at: Optional[datetime]
    hf_sentiment: Optional[str]
    hf_score: Optional[float]
    hf_justification: Optional[str] = None
    gemini_sentiment: Optional[str]
    gemini_support: Optional[str]
    gemini_score: Optional[float]
    gemini_justification: Optional[str] = None
    gemini_sarcasm_score: Optional[float] = None

    class Config:
        from_attributes = True


# Transcript Schemas
class TranscriptResponse(BaseModel):
    id: int
    video_id: int
    text: str
    language: Optional[str]
    confidence: Optional[float]
    word_count: Optional[int]
    processing_time: Optional[float]

    class Config:
        from_attributes = True


# News Article Schemas
class NewsArticleResponse(BaseModel):
    id: int
    topic_id: int
    title: str
    source: str
    source_type: Optional[str] = None
    author: Optional[str] = None
    url: str
    published_at: Optional[datetime] = None
    description: Optional[str] = None
    
    # HuggingFace Sentiment
    hf_sentiment: Optional[str] = None
    hf_score: Optional[float] = None
    
    # Gemini Sentiment
    gemini_sentiment: Optional[str] = None
    gemini_support: Optional[str] = None
    gemini_score: Optional[float] = None
    gemini_justification: Optional[str] = None
    gemini_sarcasm_score: Optional[float] = None
    hf_justification: Optional[str] = None

    # Aggregated/Overall sentiment and score breakdown
    overall_sentiment: Optional[SentimentType] = None
    positive_score: Optional[float] = None
    negative_score: Optional[float] = None
    neutral_score: Optional[float] = None
    
    # Impact Score
    impact_score: Optional[float] = None
    
    # Relevance Score (0-100, how closely article relates to topic)
    relevance_score: Optional[int] = None
    
    # Entities (JSON string)
    entities_json: Optional[str] = None
    # Backwards-compatible property name expected in some code paths
    entities: Optional[str] = None

    class Config:
        from_attributes = True
