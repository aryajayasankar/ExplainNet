from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    topic_name = Column(String(500), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    last_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    analysis_status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    total_videos = Column(Integer, default=0)  # Number of videos successfully analyzed
    total_articles = Column(Integer, default=0)  # Number of articles successfully analyzed
    videos_found = Column(Integer, default=0)  # Original search result count
    articles_found = Column(Integer, default=0)  # Original search result count
    overall_sentiment = Column(String(50), nullable=True)
    overall_impact_score = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # NEW: Source diversity metric
    unique_sources_count = Column(Integer, default=0)
    
    # AI Synthesis Cache
    ai_synthesis_cache = Column(Text, nullable=True)  # JSON string of cached AI analysis
    ai_synthesis_generated_at = Column(DateTime(timezone=True), nullable=True)  # When cache was generated
    
    # Processing Time
    processing_time_seconds = Column(Integer, nullable=True)  # Time taken to analyze in seconds

    # Relationships
    videos = relationship("Video", back_populates="topic", cascade="all, delete-orphan")
    articles = relationship("NewsArticle", back_populates="topic", cascade="all, delete-orphan")


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    video_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    channel_name = Column(String(200), nullable=False)
    channel_id = Column(String(100), nullable=True)
    subscriber_count = Column(Integer, default=0)
    thumbnail_url = Column(String(500), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    duration = Column(String(50), nullable=True)
    
    # NEW: Duration and Language for filtering
    duration_seconds = Column(Integer, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    language = Column(String(10), nullable=True, default='en')
    
    # NEW: Transcription status tracking
    transcription_status = Column(String(20), default='pending')  # pending, success, failed, timeout
    transcription_error = Column(Text, nullable=True)
    
    # NEW: Entity extraction (stored as JSON string)
    entities_json = Column(Text, nullable=True)  # {"persons": [...], "organizations": [...], "locations": [...]}
    
    # Impact Score Components
    impact_score = Column(Float, nullable=True)
    reach_score = Column(Float, nullable=True)
    engagement_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    influence_score = Column(Float, nullable=True)
    recency_boost = Column(Float, default=1.0)
    
    # Overall sentiment from both models
    overall_sentiment = Column(String(50), nullable=True)
    models_agree = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    topic = relationship("Topic", back_populates="videos")
    transcript = relationship("Transcript", back_populates="video", uselist=False, cascade="all, delete-orphan")
    sentiments = relationship("Sentiment", back_populates="video", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="video", cascade="all, delete-orphan")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), unique=True, nullable=False)
    text = Column(Text, nullable=False)
    language = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    word_count = Column(Integer, nullable=True)
    processing_time = Column(Float, nullable=True)
    has_speech = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    video = relationship("Video", back_populates="transcript")


class Sentiment(Base):
    __tablename__ = "sentiments"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    model_name = Column(String(100), nullable=False)  # 'huggingface' or 'gemini'
    sentiment = Column(String(50), nullable=False)  # POSITIVE, NEGATIVE, NEUTRAL, MIXED
    confidence = Column(Float, nullable=False)
    
    # Score breakdown
    positive_score = Column(Float, nullable=True)
    negative_score = Column(Float, nullable=True)
    neutral_score = Column(Float, nullable=True)
    
    # Gemini-specific fields
    emotional_tone = Column(String(100), nullable=True)
    emotions_json = Column(Text, nullable=True)  # JSON string: {"joy": 0-100, "sadness": 0-100, ...}
    objectivity_score = Column(Float, nullable=True)
    bias_level = Column(String(50), nullable=True)
    bias_type = Column(String(100), nullable=True)
    controversy_level = Column(String(50), nullable=True)
    evidence_quality = Column(String(50), nullable=True)
    key_themes = Column(Text, nullable=True)  # JSON string
    neutral_summary = Column(Text, nullable=True)
    # Justification and sarcasm score (when returned by models)
    gemini_justification = Column(Text, nullable=True)
    gemini_sarcasm_score = Column(Float, nullable=True)
    hf_justification = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    video = relationship("Video", back_populates="sentiments")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    comment_id = Column(String(100), unique=True, nullable=False)
    author = Column(String(200), nullable=False)
    text = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # NEW: HuggingFace Sentiment Analysis
    hf_sentiment = Column(String(50), nullable=True)  # positive, negative, neutral
    hf_score = Column(Float, nullable=True)  # confidence 0-1
    hf_justification = Column(Text, nullable=True)
    
    # NEW: Gemini Sentiment Analysis
    gemini_sentiment = Column(String(50), nullable=True)  # positive, negative, neutral
    gemini_support = Column(String(50), nullable=True)  # support, oppose, neutral
    gemini_score = Column(Float, nullable=True)
    gemini_justification = Column(Text, nullable=True)
    gemini_sarcasm_score = Column(Float, nullable=True)
    gemini_emotions_json = Column(Text, nullable=True)  # JSON string: {"joy": 0-100, ...}
    hf_emotions_json = Column(Text, nullable=True)  # JSON string for VADER emotions if needed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    video = relationship("Video", back_populates="comments")


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    source = Column(String(200), nullable=False)
    source_type = Column(String(50), nullable=True)  # 'recent' or 'historical'
    author = Column(String(200), nullable=True)
    url = Column(String(1000), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    
    # NEW: HuggingFace Sentiment
    hf_sentiment = Column(String(50), nullable=True)
    hf_score = Column(Float, nullable=True)
    
    # NEW: Gemini Sentiment
    gemini_sentiment = Column(String(50), nullable=True)
    gemini_support = Column(String(50), nullable=True)
    gemini_score = Column(Float, nullable=True)
    gemini_justification = Column(Text, nullable=True)
    gemini_sarcasm_score = Column(Float, nullable=True)
    hf_justification = Column(Text, nullable=True)

    # Overall / aggregated sentiment and score breakdown
    overall_sentiment = Column(String(50), nullable=True)
    positive_score = Column(Float, nullable=True)
    negative_score = Column(Float, nullable=True)
    neutral_score = Column(Float, nullable=True)
    
    # NEW: Impact Score
    impact_score = Column(Float, nullable=True)
    
    # NEW: Relevance Score (how closely article relates to topic, 0-100)
    relevance_score = Column(Integer, nullable=True)
    
    # NEW: Entity extraction (stored as JSON string)
    entities_json = Column(Text, nullable=True)
    # Backwards-compatible alias column used by code elsewhere
    entities = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    topic = relationship("Topic", back_populates="articles")
