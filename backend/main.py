from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, desc
from textblob import TextBlob
from . import crud, models, schemas, pipeline, database
import statistics
from datetime import datetime
from typing import Dict, List

# Try to import ml_pipeline, but don't fail if it's not available yet
try:
    from ml_pipeline import inference
    ML_PIPELINE_AVAILABLE = True
except ImportError:
    ML_PIPELINE_AVAILABLE = False
    print("Warning: ml_pipeline not available. Inference endpoint will return mock data.")

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try: 
        yield db
    finally: 
        db.close()

# Helper functions for analytics
def calculate_channel_impact_score(db: Session, source_id: int, topic_id: int = None):
    """Calculate impact score for a YouTube channel"""
    query = db.query(models.Video).filter(models.Video.source_id == source_id)
    if topic_id:
        query = query.filter(models.Video.topic_id == topic_id)
    
    videos = query.all()
    if not videos:
        return 0
    
    # Calculate metrics
    total_views = sum(int(v.view_count or 0) for v in videos)
    avg_views = total_views / len(videos) if videos else 0
    total_engagement = sum(int(v.like_count or 0) + int(v.comment_count or 0) for v in videos)
    
    # Normalize scores (simple approach - can be refined)
    view_score = min(50, avg_views / 10000)  # Max 50 points for views
    engagement_score = min(30, total_engagement / 1000)  # Max 30 points for engagement
    frequency_score = min(20, len(videos) * 2)  # Max 20 points for frequency
    
    return round(view_score + engagement_score + frequency_score, 2)

def analyze_comment_sentiment(comments):
    """Analyze sentiment of comments using TextBlob"""
    if not comments:
        return {"positive": 0, "neutral": 0, "negative": 0, "overall_score": 50, "total_comments": 0}
    
    sentiments = []
    for comment in comments:
        if comment.comment_text:
            try:
                blob = TextBlob(comment.comment_text)
                sentiments.append(blob.sentiment.polarity)
            except:
                continue
    
    if not sentiments:
        return {"positive": 0, "neutral": 0, "negative": 0, "overall_score": 50, "total_comments": len(comments)}
    
    positive = len([s for s in sentiments if s > 0.1])
    negative = len([s for s in sentiments if s < -0.1])
    neutral = len(sentiments) - positive - negative
    
    overall_score = (sum(sentiments) / len(sentiments)) * 50 + 50  # Convert to 0-100 scale
    
    return {
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "overall_score": round(max(0, min(100, overall_score)), 2),
        "total_comments": len(comments)
    }

# Existing endpoints
@app.get("/topics/", response_model=list[schemas.Topic])
def read_topics(db: Session = Depends(get_db)):
    return crud.get_topics_with_stats(db)
    
@app.get("/topics/{topic_id}/inference/", response_model=schemas.InferenceResponse)
def get_inference(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).filter(models.Topic.topic_id == topic_id).first()
    if not topic: 
        raise HTTPException(status_code=404, detail="Topic not found")
    
    if ML_PIPELINE_AVAILABLE:
        score = inference.predict_virality(topic_id=topic_id)
        if score is None: 
            raise HTTPException(status_code=404, detail="Could not generate graph.")
    else:
        # Return mock data if ML pipeline isn't available
        score = 0.75  # Mock virality score
    
    return {"topic_id": topic_id, "topic_name": topic.topic_name, "predicted_virality_score": score}

@app.get("/topics/{topic_id}/news-reliability/")
def get_news_reliability(topic_id: int, db: Session = Depends(get_db)):
    data = crud.get_news_reliability_for_topic(db, topic_id=topic_id)
    if not data: 
        raise HTTPException(status_code=404, detail="No recent news found.")
    return data

# NEW ENHANCED ANALYTICS ENDPOINTS
@app.get("/topics/{topic_id}/channel-analytics/")
def get_channel_analytics(topic_id: int, db: Session = Depends(get_db)):
    """Get comprehensive YouTube channel analytics for a topic"""
    channels = db.query(models.Source).filter(
        models.Source.platform == "YouTube"
    ).join(models.Video).filter(models.Video.topic_id == topic_id).distinct().all()
    
    channel_data = []
    for channel in channels:
        videos = db.query(models.Video).filter(
            models.Video.source_id == channel.source_id,
            models.Video.topic_id == topic_id
        ).all()
        
        if videos:
            impact_score = calculate_channel_impact_score(db, channel.source_id, topic_id)
            total_views = sum(int(v.view_count or 0) for v in videos)
            total_videos = len(videos)
            avg_views = total_views / total_videos if total_videos > 0 else 0
            
            # Get all comments for sentiment analysis
            all_comments = []
            for video in videos:
                comments = db.query(models.Comment).filter(models.Comment.video_id == video.video_id).all()
                all_comments.extend(comments)
            
            sentiment = analyze_comment_sentiment(all_comments)
            
            channel_data.append({
                "source_id": channel.source_id,
                "channel_name": channel.source_name,
                "impact_score": impact_score,
                "total_videos": total_videos,
                "total_views": total_views,
                "avg_views_per_video": round(avg_views, 2),
                "sentiment_analysis": sentiment
            })
    
    # Sort by impact score
    channel_data.sort(key=lambda x: x["impact_score"], reverse=True)
    return channel_data

@app.get("/topics/{topic_id}/video-timeline/")
def get_video_timeline(topic_id: int, db: Session = Depends(get_db)):
    """Get video timeline data for views vs publication date chart"""
    videos = db.query(models.Video).filter(
        models.Video.topic_id == topic_id
    ).order_by(models.Video.publication_date).all()
    
    timeline_data = []
    for video in videos:
        if video.publication_date and video.view_count:
            source = db.query(models.Source).filter(models.Source.source_id == video.source_id).first()
            timeline_data.append({
                "video_id": video.video_id,
                "title": video.title,
                "publication_date": video.publication_date.isoformat(),
                "view_count": int(video.view_count or 0),
                "channel_name": source.source_name if source else "Unknown",
                "url": video.url
            })
    
    return timeline_data

@app.get("/topics/{topic_id}/news-data/")
def get_news_data(topic_id: int, db: Session = Depends(get_db)):
    """Get all news data (both Guardian and NewsAPI) for a topic"""
    # Guardian articles
    guardian_articles = db.query(models.Article).filter(
        models.Article.topic_id == topic_id,
        models.Article.data_source_api == "Guardian"
    ).order_by(desc(models.Article.publication_date)).all()
    
    # NewsAPI articles
    newsapi_articles = db.query(models.Article).filter(
        models.Article.topic_id == topic_id,
        models.Article.data_source_api == "NewsAPI.org"
    ).order_by(desc(models.Article.publication_date)).all()
    
    guardian_data = [{
        "article_id": article.article_id,
        "headline": article.headline,
        "url": article.url,
        "author": article.author,
        "publication_date": article.publication_date.isoformat() if article.publication_date else None,
        "source_name": "The Guardian"
    } for article in guardian_articles]
    
    newsapi_data = []
    for article in newsapi_articles:
        source = db.query(models.Source).filter(models.Source.source_id == article.source_id).first()
        newsapi_data.append({
            "article_id": article.article_id,
            "headline": article.headline,
            "url": article.url,
            "author": article.author,
            "publication_date": article.publication_date.isoformat() if article.publication_date else None,
            "source_name": source.source_name if source else "Unknown"
        })
    
    return {
        "guardian": guardian_data,
        "newsapi": newsapi_data,
        "guardian_count": len(guardian_data),
        "newsapi_count": len(newsapi_data)
    }

@app.get("/topics/{topic_id}/youtube-data/")
def get_youtube_data(topic_id: int, db: Session = Depends(get_db)):
    """Get YouTube video data for a topic"""
    videos = db.query(models.Video).filter(
        models.Video.topic_id == topic_id
    ).order_by(desc(models.Video.publication_date)).all()
    
    video_data = []
    for video in videos:
        source = db.query(models.Source).filter(models.Source.source_id == video.source_id).first()
        video_data.append({
            "video_id": video.video_id,
            "title": video.title,
            "url": video.url,
            "publication_date": video.publication_date.isoformat() if video.publication_date else None,
            "channel_name": source.source_name if source else "Unknown",
            "view_count": int(video.view_count or 0),
            "like_count": int(video.like_count or 0),
            "comment_count": int(video.comment_count or 0)
        })
    
    return {
        "videos": video_data,
        "total_videos": len(video_data)
    }

# Enhanced reliability endpoint
@app.get("/topics/{topic_id}/enhanced-news-reliability/")
def get_enhanced_news_reliability(topic_id: int, db: Session = Depends(get_db)):
    """Enhanced news reliability with more detailed metrics"""
    base_data = crud.get_news_reliability_for_topic(db, topic_id=topic_id)
    
    # Add more detailed metrics
    enhanced_data = []
    for source_info in base_data:
        source_id = source_info["source_id"]
        
        # Get all articles from this source
        articles = db.query(models.Article).filter(
            models.Article.source_id == source_id,
            models.Article.topic_id == topic_id
        ).all()
        
        enhanced_info = source_info.copy()
        enhanced_info.update({
            "total_articles": len(articles),
            "avg_article_length": statistics.mean([len(a.full_text or "") for a in articles]) if articles else 0,
            "has_author_info": sum(1 for a in articles if a.author) / len(articles) * 100 if articles else 0
        })
        enhanced_data.append(enhanced_info)
    
    return enhanced_data

# Existing endpoints continue...
@app.post("/topics/{topic_id}/fetch-historical-news/")
def fetch_historical_news(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).filter(models.Topic.topic_id == topic_id).first()
    if not topic: 
        raise HTTPException(status_code=404, detail="Topic not found")
    
    articles = pipeline.collect_guardian_data(topic.topic_name)
    if articles:
        source = crud.get_or_create_source(db, source_name="The Guardian", platform="News")
        for article in articles:
            if not db.query(models.Article).filter(models.Article.url == article['url']).first():
                crud.create_article(db, article=article, topic_id=topic.topic_id, source_id=source.source_id)
    
    return {"status": "success", "message": f"Fetched {len(articles)} historical articles."}

@app.post("/topics/{topic_id}/fetch-recent-news/")
def fetch_recent_news(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).filter(models.Topic.topic_id == topic_id).first()
    if not topic: 
        raise HTTPException(status_code=404, detail="Topic not found")
    
    articles = pipeline.collect_newsapi_org_data(country='us')
    if articles:
        for article_data in articles:
            if not db.query(models.Article).filter(models.Article.url == article_data['url']).first():
                source_name = article_data.get('source_name') or "Unknown Source"
                source = crud.get_or_create_source(db, source_name=source_name, platform="News")
                crud.create_article(db, article=article_data, topic_id=topic.topic_id, source_id=source.source_id)
    
    return {"status": "success", "message": f"Fetched {len(articles)} recent articles."}

@app.post("/analyze/")
def analyze_topic(req: schemas.TopicCreate, db: Session = Depends(get_db)):
    topic = crud.get_or_create_topic(db, topic_name=req.topic_name)
    
    print("--- Starting Initial Data Collection (YouTube only) ---")
    youtube_videos = pipeline.collect_youtube_data(req.topic_name)
    print("--- YouTube Collection Finished ---")

    if youtube_videos:
        for video_data in youtube_videos:
            source = crud.get_or_create_source(db, source_name=video_data['channel_name'], platform="YouTube")
            crud.create_video_with_comments(db, video=video_data, topic_id=topic.topic_id, source_id=source.source_id)
        print(f"Saved {len(youtube_videos)} videos and their comments to DB.")
    
    return {"status": "success", "topic_id": topic.topic_id, "message": "Initial analysis complete."}