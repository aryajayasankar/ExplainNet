# Supabase Database Schema Creation
# Run this in Supabase SQL Editor after creating your project

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Topics table
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    topic_name VARCHAR(500) NOT NULL,
    analysis_status VARCHAR(50) DEFAULT 'pending',
    total_videos INTEGER DEFAULT 0,
    total_articles INTEGER DEFAULT 0,
    videos_found INTEGER DEFAULT 0,
    articles_found INTEGER DEFAULT 0,
    overall_sentiment VARCHAR(50),
    overall_impact_score FLOAT,
    unique_sources_count INTEGER DEFAULT 0,
    processing_time_seconds FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    ai_synthesis_cache TEXT,
    ai_synthesis_generated_at TIMESTAMP WITH TIME ZONE
);

-- Videos table
CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    video_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    channel_name VARCHAR(200) NOT NULL,
    channel_id VARCHAR(100),
    subscriber_count INTEGER DEFAULT 0,
    thumbnail_url VARCHAR(500),
    published_at TIMESTAMP WITH TIME ZONE,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    duration VARCHAR(50),
    duration_seconds INTEGER,
    duration_minutes FLOAT,
    language VARCHAR(10) DEFAULT 'en',
    transcription_status VARCHAR(20) DEFAULT 'pending',
    transcription_error TEXT,
    entities_json TEXT,
    emotions_json TEXT,
    impact_score FLOAT,
    reach_score FLOAT,
    engagement_score FLOAT,
    sentiment_score FLOAT,
    quality_score FLOAT,
    influence_score FLOAT,
    recency_boost FLOAT DEFAULT 1.0,
    overall_sentiment VARCHAR(50),
    models_agree BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
    id SERIAL PRIMARY KEY,
    video_id INTEGER UNIQUE NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    language VARCHAR(50),
    confidence FLOAT,
    word_count INTEGER,
    processing_time FLOAT,
    has_speech BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sentiments table
CREATE TABLE IF NOT EXISTS sentiments (
    id SERIAL PRIMARY KEY,
    video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    model_name VARCHAR(50) NOT NULL,
    sentiment VARCHAR(50) NOT NULL,
    confidence FLOAT,
    positive_score FLOAT,
    negative_score FLOAT,
    neutral_score FLOAT,
    emotional_tone VARCHAR(200),
    objectivity_score FLOAT,
    bias_level VARCHAR(50),
    bias_type VARCHAR(100),
    controversy_level VARCHAR(50),
    evidence_quality VARCHAR(50),
    key_themes TEXT,
    neutral_summary TEXT,
    hf_justification TEXT,
    gemini_justification TEXT,
    gemini_sarcasm_score FLOAT,
    emotions_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comments table
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    comment_id VARCHAR(100) UNIQUE NOT NULL,
    author VARCHAR(200),
    text TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    published_at TIMESTAMP WITH TIME ZONE,
    sentiment VARCHAR(50),
    toxicity_score FLOAT,
    hf_sentiment VARCHAR(50),
    hf_score FLOAT,
    hf_justification TEXT,
    gemini_sentiment VARCHAR(50),
    gemini_support VARCHAR(200),
    gemini_score FLOAT,
    gemini_justification TEXT,
    gemini_sarcasm_score FLOAT,
    gemini_emotions_json TEXT,
    hf_emotions_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- News Articles table
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    url VARCHAR(1000) UNIQUE NOT NULL,
    source VARCHAR(200) NOT NULL,
    source_type VARCHAR(50),
    author VARCHAR(200),
    published_at TIMESTAMP WITH TIME ZONE,
    content TEXT,
    hf_sentiment VARCHAR(50),
    hf_score FLOAT,
    gemini_sentiment VARCHAR(50),
    gemini_support VARCHAR(200),
    gemini_score FLOAT,
    gemini_justification TEXT,
    gemini_sarcasm_score FLOAT,
    hf_justification TEXT,
    impact_score FLOAT,
    entities_json TEXT,
    relevance_score FLOAT,
    overall_sentiment VARCHAR(50),
    positive_score FLOAT,
    negative_score FLOAT,
    neutral_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_videos_topic_id ON videos(topic_id);
CREATE INDEX IF NOT EXISTS idx_videos_video_id ON videos(video_id);
CREATE INDEX IF NOT EXISTS idx_sentiments_video_id ON sentiments(video_id);
CREATE INDEX IF NOT EXISTS idx_comments_video_id ON comments(video_id);
CREATE INDEX IF NOT EXISTS idx_news_articles_topic_id ON news_articles(topic_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_video_id ON transcripts(video_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger to videos table
CREATE TRIGGER update_videos_updated_at BEFORE UPDATE ON videos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE topics IS 'Main topics for analysis';
COMMENT ON TABLE videos IS 'YouTube videos related to topics';
COMMENT ON TABLE transcripts IS 'Video transcriptions';
COMMENT ON TABLE sentiments IS 'Sentiment analysis results from different models';
COMMENT ON TABLE comments IS 'YouTube comments with sentiment analysis';
COMMENT ON TABLE news_articles IS 'News articles related to topics';
