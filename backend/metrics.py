from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import numpy as np

try:
    from . import models
except ImportError:
    import models

def calculate_channel_impact_score(db: Session, channel_id: int) -> float:
    """Calculate impact score for a YouTube channel based on multiple factors"""
    videos = db.query(models.Video).filter(models.Video.source_id == channel_id).all()
    
    if not videos:
        return 0.0
    
    # Calculate speed factor (average time to first upload per topic)
    topics = set(video.topic_id for video in videos)
    speed_factors = []
    for topic_id in topics:
        topic_videos = [v for v in videos if v.topic_id == topic_id]
        if topic_videos:
            first_video = min(topic_videos, key=lambda x: x.publication_date)
            topic = db.query(models.Topic).filter(models.Topic.topic_id == topic_id).first()
            if topic:
                speed_factors.append(1.0)  # Placeholder for actual calculation

    speed_factor = np.mean(speed_factors) if speed_factors else 0.0
    
    # Calculate frequency factor
    frequency_factor = len(videos) / len(topics) if topics else 0
    
    # Calculate engagement factor
    engagement_scores = []
    for video in videos:
        if video.publication_date:
            days_since_pub = (datetime.now() - video.publication_date).days
            if days_since_pub > 0:
                engagement = (
                    (video.view_count or 0) + 
                    (video.like_count or 0) * 2 + 
                    (video.comment_count or 0) * 3
                ) / days_since_pub
                engagement_scores.append(engagement)
    
    engagement_factor = np.mean(engagement_scores) if engagement_scores else 0.0
    
    # Normalize engagement factor (0-1 scale)
    max_engagement = 1000000  # Adjust based on your data
    engagement_factor = min(engagement_factor / max_engagement, 1.0)
    
    # Calculate final impact score
    impact_score = (
        0.4 * speed_factor +
        0.3 * frequency_factor +
        0.3 * engagement_factor
    )
    
    return impact_score

def calculate_news_source_reliability(db: Session, source_id: int) -> dict:
    """Calculate reliability metrics for a news source"""
    articles = db.query(models.Article).filter(models.Article.source_id == source_id).all()
    
    if not articles:
        return {
            "reliabilityScore": 0.0,
            "speedFactor": 0.0,
            "consistencyFactor": 0.0
        }
    
    # Calculate speed factor
    topics = set(article.topic_id for article in articles)
    speed_scores = []
    for topic_id in topics:
        topic_articles = [a for a in articles if a.topic_id == topic_id]
        if topic_articles:
            first_article = min(topic_articles, key=lambda x: x.publication_date)
            speed_scores.append(first_article.time_to_publish or 0)
    
    speed_factor = 1 / (np.mean(speed_scores) + 1) if speed_scores else 0
    
    # Calculate consistency factor
    pub_intervals = []
    sorted_articles = sorted(articles, key=lambda x: x.publication_date)
    for i in range(1, len(sorted_articles)):
        if sorted_articles[i].publication_date and sorted_articles[i-1].publication_date:
            interval = (sorted_articles[i].publication_date - sorted_articles[i-1].publication_date).total_seconds()
            pub_intervals.append(interval)
    
    consistency_factor = 1 - np.std(pub_intervals) / (max(pub_intervals) if pub_intervals else 1)
    
    # Calculate final reliability score
    reliability_score = (
        0.35 * speed_factor +
        0.25 * len(topics) / db.query(models.Topic).count() +  # Coverage factor
        0.2 * consistency_factor +
        0.2 * len(articles) / db.query(models.Article).count()  # Volume factor
    )
    
    return {
        "reliabilityScore": reliability_score,
        "speedFactor": speed_factor,
        "consistencyFactor": consistency_factor
    }

def get_views_timeline(db: Session, topic_id: int) -> dict:
    """Get timeline data for video views by channel"""
    videos = db.query(models.Video).filter(models.Video.topic_id == topic_id).all()
    
    if not videos:
        return {"dates": [], "views": [], "channels": []}
    
    # Group videos by channel
    channel_videos = {}
    for video in videos:
        source = db.query(models.Source).filter(models.Source.source_id == video.source_id).first()
        if source:
            if source.source_name not in channel_videos:
                channel_videos[source.source_name] = []
            channel_videos[source.source_name].append(video)
    
    # Prepare timeline data
    all_dates = sorted(list(set(
        video.publication_date.strftime("%Y-%m-%d")
        for videos in channel_videos.values()
        for video in videos
        if video.publication_date
    )))
    
    channels = list(channel_videos.keys())
    views_data = []
    
    for channel in channels:
        channel_views = []
        for date in all_dates:
            date_views = sum(
                video.view_count or 0
                for video in channel_videos[channel]
                if video.publication_date and video.publication_date.strftime("%Y-%m-%d") == date
            )
            channel_views.append(date_views)
        views_data.append(channel_views)
    
    return {
        "dates": all_dates,
        "views": views_data,
        "channels": channels
    }

def calculate_sentiment_metrics(db: Session, topic_id: int) -> list:
    """Calculate sentiment metrics for video comments"""
    videos = db.query(models.Video).filter(models.Video.topic_id == topic_id).all()
    sentiment_data = []
    
    for video in videos:
        comments = db.query(models.Comment).filter(models.Comment.video_id == video.video_id).all()
        if comments:
            avg_sentiment = np.mean([comment.sentiment_score or 0 for comment in comments])
            avg_engagement = np.mean([comment.engagement_weight or 0 for comment in comments])
            
            sentiment_data.append({
                "videoId": video.video_id,
                "sentimentScore": float(avg_sentiment),
                "engagementScore": float(avg_engagement)
            })
    
    return sentiment_data