from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from datetime import datetime


def get_topics(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Topic).order_by(models.Topic.created_at.desc()).offset(skip).limit(limit).all()


def get_topic(db: Session, topic_id: int):
    return db.query(models.Topic).filter(models.Topic.id == topic_id).first()


def create_topic(db: Session, topic):
    db_topic = models.Topic(topic_name=topic.topic_name, analysis_status="pending")
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic


def update_topic_status(db: Session, topic_id: int, status: str, error_message: str = None):
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if topic:
        topic.analysis_status = status
        topic.last_analyzed_at = datetime.now()
        if error_message:
            topic.error_message = error_message
        db.commit()
        db.refresh(topic)
    return topic


def delete_topic(db: Session, topic_id: int):
    topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
    if topic:
        db.delete(topic)
        db.commit()
        return True
    return False


def create_video(db: Session, video_data: dict, topic_id: int):
    # If a video with the same external `video_id` already exists, update and return it
    vid = video_data.get('video_id')
    if vid:
        existing = db.query(models.Video).filter(models.Video.video_id == vid).first()
        if existing:
            # Update only allowed columns to avoid unexpected attributes
            allowed_cols = {c.name for c in models.Video.__table__.columns}
            for k, v in video_data.items():
                if k in allowed_cols and k != 'id':
                    setattr(existing, k, v)
            existing.topic_id = topic_id
            db.commit()
            db.refresh(existing)
            return existing

    db_video = models.Video(topic_id=topic_id, **video_data)
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video


def get_videos_by_topic(db: Session, topic_id: int):
    return db.query(models.Video).filter(models.Video.topic_id == topic_id).all()


def get_video(db: Session, video_id: int):
    return db.query(models.Video).filter(models.Video.id == video_id).first()


def update_video_scores(db: Session, video_id: int, scores: dict):
    video = db.query(models.Video).filter(models.Video.id == video_id).first()
    if video:
        for key, value in scores.items():
            setattr(video, key, value)
        db.commit()
        db.refresh(video)
    return video


def create_transcript(db: Session, transcript_data: dict, video_id: int):
    # Remove fields not in the Transcript model (like 'source', 'status', 'duration')
    transcript_data_for_db = {k: v for k, v in transcript_data.items() if k not in ['source', 'status', 'duration']}
    
    # Check if transcript already exists for this video
    existing = db.query(models.Transcript).filter(models.Transcript.video_id == video_id).first()
    if existing:
        # Update existing transcript
        for key, value in transcript_data_for_db.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new transcript
    db_transcript = models.Transcript(video_id=video_id, **transcript_data_for_db)
    db.add(db_transcript)
    db.commit()
    db.refresh(db_transcript)
    return db_transcript


def create_sentiment(db: Session, sentiment_data: dict, video_id: int):
    # Normalize keys and remove unexpected fields
    if not isinstance(sentiment_data, dict):
        sentiment_data = {}

    data = {k: v for k, v in sentiment_data.items() if k != 'error'}

    # If the model returned no sentiment (None), mark it as UNKNOWN so DB constraints are satisfied
    if data.get('sentiment') is None:
        data['sentiment'] = 'UNKNOWN'
    # Ensure confidence exists
    if 'confidence' not in data or data.get('confidence') is None:
        data['confidence'] = 0.0

    model_name = (data.get('model_name') or '').lower()
    # Map generic 'justification' to model-specific column names
    if 'justification' in data:
        if 'huggingface' in model_name:
            data['hf_justification'] = data.pop('justification')
        elif 'gemini' in model_name:
            data['gemini_justification'] = data.pop('justification')

    # Map generic sarcasm_score to gemini_sarcasm_score
    if 'sarcasm_score' in data and 'gemini' in model_name:
        data['gemini_sarcasm_score'] = data.get('sarcasm_score')

    # Only include columns that exist on the Sentiment model
    allowed_cols = {c.name for c in models.Sentiment.__table__.columns}
    filtered = {k: v for k, v in data.items() if k in allowed_cols}

    db_sentiment = models.Sentiment(video_id=video_id, **filtered)
    db.add(db_sentiment)
    db.commit()
    db.refresh(db_sentiment)
    return db_sentiment


def get_sentiments_by_video(db: Session, video_id: int):
    return db.query(models.Sentiment).filter(models.Sentiment.video_id == video_id).all()


def create_comment(db: Session, comment_data: dict, video_id: int):
    # Only include allowed columns to avoid unexpected kwargs
    allowed_cols = {c.name for c in models.Comment.__table__.columns}
    filtered = {k: v for k, v in comment_data.items() if k in allowed_cols}
    
    # Check if comment already exists (by comment_id)
    comment_id = filtered.get('comment_id')
    if comment_id:
        existing = db.query(models.Comment).filter(models.Comment.comment_id == comment_id).first()
        if existing:
            # Update existing comment
            for key, value in filtered.items():
                if key != 'comment_id':  # Don't update the ID itself
                    setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
    
    # Create new comment
    db_comment = models.Comment(video_id=video_id, **filtered)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comments_by_video(db: Session, video_id: int, limit: int = 100):
    return db.query(models.Comment).filter(models.Comment.video_id == video_id).limit(limit).all()


def create_article(db: Session, article_data: dict, topic_id: int):
    # Filter article_data to only columns present in the NewsArticle model to avoid unexpected kwargs
    allowed_cols = {c.name for c in models.NewsArticle.__table__.columns}
    filtered = {k: v for k, v in article_data.items() if k in allowed_cols}
    db_article = models.NewsArticle(topic_id=topic_id, **filtered)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article


def get_articles_by_topic(db: Session, topic_id: int):
    return db.query(models.NewsArticle).filter(models.NewsArticle.topic_id == topic_id).all()
