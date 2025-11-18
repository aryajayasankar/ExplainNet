from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
from typing import List
from .database import engine, Base, get_db
from . import models
from . import schemas
from . import crud
from . import pipeline
from . import cache_service

load_dotenv()

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ExplainNet API",
    description="Comprehensive topic analysis platform",
    version="1.0.0"
)

# Configure CORS origins via environment variable for flexibility in dev/prod
allow_origins_env = os.getenv("ALLOW_ORIGINS")
if allow_origins_env:
    # Expect comma-separated list
    allow_origins = [o.strip() for o in allow_origins_env.split(',') if o.strip()]
else:
    # Default: typical Angular dev server origins
    allow_origins = ["http://localhost:4200", "http://127.0.0.1:4200"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "ExplainNet API", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# TOPIC ENDPOINTS
@app.post("/api/topics", response_model=schemas.TopicResponse)
async def create_topic(
    topic: schemas.TopicCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new topic and start analysis in background"""
    
    # Create topic
    db_topic = crud.create_topic(db, topic)
    
    # Start analysis in background
    background_tasks.add_task(pipeline.analyze_topic, db, db_topic.id, topic.topic_name)
    
    return db_topic


@app.get("/api/topics", response_model=List[schemas.TopicResponse])
async def get_topics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all topics"""
    topics = crud.get_topics(db, skip=skip, limit=limit)
    return topics


@app.get("/api/topics/{topic_id}", response_model=schemas.TopicResponse)
async def get_topic(topic_id: int, db: Session = Depends(get_db)):
    """Get a specific topic"""
    topic = crud.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@app.delete("/api/topics/{topic_id}")
async def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    """Delete a topic"""
    success = crud.delete_topic(db, topic_id)
    if not success:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"message": "Topic deleted successfully"}


# VIDEO ENDPOINTS
@app.get("/api/topics/{topic_id}/videos", response_model=List[schemas.VideoResponse])
async def get_topic_videos(topic_id: int, db: Session = Depends(get_db)):
    """Get all videos for a topic"""
    videos = crud.get_videos_by_topic(db, topic_id)
    return videos


@app.get("/api/videos/{video_id}", response_model=schemas.VideoResponse)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """Get a specific video with all details"""
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@app.get("/api/videos/{video_id}/sentiments", response_model=List[schemas.SentimentResponse])
async def get_video_sentiments(video_id: int, db: Session = Depends(get_db)):
    """Get sentiment analyses for a video"""
    sentiments = crud.get_sentiments_by_video(db, video_id)
    return sentiments


@app.get("/api/videos/{video_id}/comments", response_model=List[schemas.CommentResponse])
async def get_video_comments(video_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """Get comments for a video"""
    comments = crud.get_comments_by_video(db, video_id, limit=limit)
    return comments


@app.get("/api/videos/{video_id}/transcript", response_model=schemas.TranscriptResponse)
async def get_video_transcript(video_id: int, db: Session = Depends(get_db)):
    """Get transcript for a video"""
    video = crud.get_video(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if not video.transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return video.transcript


# ARTICLE ENDPOINTS
@app.get("/api/topics/{topic_id}/articles", response_model=List[schemas.NewsArticleResponse])
async def get_topic_articles(topic_id: int, db: Session = Depends(get_db)):
    """Get all articles for a topic"""
    articles = crud.get_articles_by_topic(db, topic_id)
    return articles


# ANALYSIS TAB ENDPOINTS
@app.get("/api/topics/{topic_id}/videos-analysis")
async def get_videos_analysis(topic_id: int, db: Session = Depends(get_db)):
    """Get comprehensive video analysis for Videos tab"""
    videos = crud.get_videos_by_topic(db, topic_id)
    
    result = {
        "total_videos": len(videos),
        "videos": []
    }
    
    for video in videos:
        video_data = {
            "id": video.id,
            "video_id": video.video_id,
            "title": video.title,
            "channel_title": video.channel_name,
            "published_at": video.published_at,
            "thumbnail_url": video.thumbnail_url,
            "view_count": video.view_count,
            "like_count": video.like_count,
            "comment_count": video.comment_count,
            "duration": video.duration,
            "impact_score": video.impact_score,
            "overall_sentiment": video.overall_sentiment,
            "transcript": None,
            "sentiments": [],
            "comments": []
        }
        
        # Add transcript if available
        if video.transcript:
            video_data["transcript"] = {
                "text": video.transcript.text,
                "word_count": video.transcript.word_count,
                "processing_time": video.transcript.processing_time
            }
        
        # Add sentiments
        if video.sentiments:
            video_data["sentiments"] = [
                {
                    "id": s.id,
                    "model_name": s.model_name,
                    "sentiment": s.sentiment,
                    "positive_score": s.positive_score,
                    "negative_score": s.negative_score,
                    "neutral_score": s.neutral_score,
                    "confidence": s.confidence,
                    "hf_justification": getattr(s, 'hf_justification', None),
                    "gemini_justification": getattr(s, 'gemini_justification', None),
                    "gemini_sarcasm_score": getattr(s, 'gemini_sarcasm_score', None),
                    "created_at": s.created_at.isoformat() if hasattr(s, 'created_at') and s.created_at is not None else None
                }
                for s in video.sentiments
            ]
        
        # Add comments with sentiments
        if video.comments:
            video_data["comments"] = [
                {
                    "id": c.id,
                    "author": c.author,
                    "text": c.text,
                    "like_count": c.like_count,
                    "published_at": c.published_at,
                    "hf_sentiment": c.hf_sentiment,
                    "hf_score": c.hf_score,
                    "gemini_sentiment": c.gemini_sentiment,
                    "gemini_score": c.gemini_score
                }
                for c in video.comments[:20]  # Limit to first 20 comments
            ]
        
        result["videos"].append(video_data)
    
    return result


@app.get("/api/topics/{topic_id}/news-analysis")
async def get_news_analysis(topic_id: int, db: Session = Depends(get_db)):
    """Get comprehensive news analysis for News tab"""
    articles = crud.get_articles_by_topic(db, topic_id)
    
    # Group by source
    sources = {}
    # Include 'unknown' for articles without an overall_sentiment
    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0, "unknown": 0}
    
    for article in articles:
        # Count by source
        source = article.source or "Unknown"
        if source not in sources:
            sources[source] = 0
        sources[source] += 1
        
        # Count sentiments: treat missing overall_sentiment as 'unknown'
        sentiment = article.overall_sentiment.lower() if article.overall_sentiment else "unknown"
        if sentiment in sentiment_distribution:
            sentiment_distribution[sentiment] += 1
    
    result = {
        "total_articles": len(articles),
        "unique_sources": len(sources),
        "sources": sources,
        "sentiment_distribution": sentiment_distribution,
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "source": a.source,
                "author": a.author,
                "published_at": a.published_at,
                "url": a.url,
                "description": a.description,
                "overall_sentiment": a.overall_sentiment,
                "positive_score": a.positive_score,
                "negative_score": a.negative_score,
                "neutral_score": a.neutral_score,
                "entities": a.entities,
                "hf_justification": getattr(a, 'hf_justification', None),
                "gemini_justification": getattr(a, 'gemini_justification', None),
                "gemini_sarcasm_score": getattr(a, 'gemini_sarcasm_score', None),
                "hf_sentiment": a.hf_sentiment,
                "gemini_sentiment": a.gemini_sentiment
            }
            for a in articles
        ]
    }
    
    return result


@app.get("/api/topics/{topic_id}/ai-summary")
async def get_ai_summary(topic_id: int, db: Session = Depends(get_db)):
    """Get AI-generated summary comparing videos vs news for AI Analysis tab"""
    topic = crud.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    videos = crud.get_videos_by_topic(db, topic_id)
    articles = crud.get_articles_by_topic(db, topic_id)
    
    # Calculate video sentiment distribution
    video_sentiments = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0, "unknown": 0}
    for video in videos:
        sentiment = video.overall_sentiment.lower() if video.overall_sentiment else "unknown"
        if sentiment in video_sentiments:
            video_sentiments[sentiment] += 1
    
    # Calculate news sentiment distribution
    news_sentiments = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0, "unknown": 0}
    for article in articles:
        sentiment = article.overall_sentiment.lower() if article.overall_sentiment else "unknown"
        if sentiment in news_sentiments:
            news_sentiments[sentiment] += 1
    
    # Calculate average impact score
    impact_scores = [v.impact_score for v in videos if v.impact_score]
    avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0
    
    # Extract common entities from news
    all_entities = []
    for article in articles:
        if article.entities:
            import json
            try:
                entities = json.loads(article.entities) if isinstance(article.entities, str) else article.entities
                if isinstance(entities, list):
                    all_entities.extend(entities)
            except:
                pass
    
    # Count entity frequency
    entity_counts = {}
    for entity in all_entities:
        entity_text = entity.get("text", "") if isinstance(entity, dict) else str(entity)
        if entity_text:
            entity_counts[entity_text] = entity_counts.get(entity_text, 0) + 1
    
    # Get top 10 entities
    top_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    result = {
        "topic_name": topic.topic_name,
        "overall_impact_score": topic.overall_impact_score or avg_impact,
        "total_videos": len(videos),
        "total_articles": len(articles),
        "video_sentiment_distribution": video_sentiments,
        "news_sentiment_distribution": news_sentiments,
        "sentiment_agreement": {
            "description": "Comparing dominant sentiment between videos and news",
            "video_dominant": max(video_sentiments, key=video_sentiments.get) if video_sentiments else "unknown",
            "news_dominant": max(news_sentiments, key=news_sentiments.get) if news_sentiments else "unknown",
            "aligned": max(video_sentiments, key=video_sentiments.get) == max(news_sentiments, key=news_sentiments.get)
        },
        "top_entities": [{"text": text, "count": count} for text, count in top_entities],
        "key_insights": [
            f"Analyzed {len(videos)} videos and {len(articles)} news articles",
            f"Average video impact score: {avg_impact:.1f}/10",
            f"Videos are predominantly {max(video_sentiments, key=video_sentiments.get).upper()}" if video_sentiments else "",
            f"News coverage is predominantly {max(news_sentiments, key=news_sentiments.get).upper()}" if news_sentiments else "",
            f"Sentiment alignment: {'ALIGNED' if max(video_sentiments, key=video_sentiments.get) == max(news_sentiments, key=news_sentiments.get) else 'DIVERGENT'}" if video_sentiments and news_sentiments else ""
        ]
    }
    
    return result


@app.get("/api/topics/{topic_id}/ai-synthesis")
async def get_ai_synthesis(topic_id: int, db: Session = Depends(get_db)):
    """
    Generate comprehensive AI synthesis combining all analytics data using Gemini.
    Returns executive summary, key trends, surprising findings, and recommendations.
    """
    topic = crud.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    videos = crud.get_videos_by_topic(db, topic_id)
    articles = crud.get_articles_by_topic(db, topic_id)
    
    # Build comprehensive topic data
    video_data = []
    for video in videos:
        # Get sentiments
        sentiments_list = db.query(models.Sentiment).filter(models.Sentiment.video_id == video.id).all()
        gemini_sentiment = None
        hf_sentiment = None
        emotions_json = None
        
        for sent in sentiments_list:
            if sent.model_name == "gemini":
                gemini_sentiment = sent.sentiment
                emotions_json = sent.emotions_json
            elif sent.model_name in ["huggingface", "vader"]:
                hf_sentiment = sent.sentiment
        
        video_data.append({
            "title": video.title,
            "view_count": video.view_count,
            "like_count": video.like_count,
            "impact_score": video.impact_score,
            "gemini_sentiment": gemini_sentiment,
            "hf_sentiment": hf_sentiment,
            "emotions": emotions_json,
            "channel": video.channel_name
        })
    
    article_data = []
    for article in articles:
        article_data.append({
            "title": article.title,
            "source": article.source,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "relevance_score": article.relevance_score if hasattr(article, 'relevance_score') else 50
        })
    
    # Prepare data for Gemini
    topic_data = {
        "topic_name": topic.topic_name,
        "videos": video_data,
        "articles": article_data,
        "analysis_date": topic.last_analyzed_at.isoformat() if topic.last_analyzed_at else None
    }
    
    # Call Gemini to generate synthesis
    from . import gemini_service
    synthesis = await gemini_service.generate_ai_synthesis(topic_data)
    
    return synthesis


# DATABASE MANAGEMENT ENDPOINTS
@app.get("/api/admin/database-stats")
async def get_database_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    stats = {
        "total_topics": db.query(models.Topic).count(),
        "total_videos": db.query(models.Video).count(),
        "total_articles": db.query(models.NewsArticle).count(),
        "total_sentiments": db.query(models.Sentiment).count(),
        "total_comments": db.query(models.Comment).count(),
        "total_transcripts": db.query(models.Transcript).count(),
        "topics": []
    }
    
    # Get detailed topic info
    topics = db.query(models.Topic).all()
    for topic in topics:
        topic_info = {
            "id": topic.id,
            "name": topic.topic_name,
            "status": topic.analysis_status,
            "videos_count": db.query(models.Video).filter(models.Video.topic_id == topic.id).count(),
            "articles_count": db.query(models.NewsArticle).filter(models.NewsArticle.topic_id == topic.id).count(),
            "created_at": topic.created_at.isoformat() if topic.created_at else None
        }
        stats["topics"].append(topic_info)
    
    return stats


@app.delete("/api/admin/clear-database")
async def clear_database(db: Session = Depends(get_db)):
    """Clear entire database (delete all data)"""
    try:
        # Delete in correct order to avoid foreign key constraints
        db.query(models.Comment).delete()
        db.query(models.Sentiment).delete()
        db.query(models.Transcript).delete()
        db.query(models.Video).delete()
        db.query(models.NewsArticle).delete()
        db.query(models.Topic).delete()
        db.commit()
        return {"message": "Database cleared successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing database: {str(e)}")


@app.delete("/api/admin/clear-topic-data/{topic_id}")
async def clear_topic_data(topic_id: int, db: Session = Depends(get_db)):
    """Clear all data for a specific topic (videos, articles, sentiments, etc.)"""
    topic = crud.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    try:
        # Get all videos for this topic
        videos = crud.get_videos_by_topic(db, topic_id)
        video_ids = [v.id for v in videos]
        
        # Delete related data
        if video_ids:
            db.query(models.Comment).filter(models.Comment.video_id.in_(video_ids)).delete(synchronize_session=False)
            db.query(models.Sentiment).filter(models.Sentiment.video_id.in_(video_ids)).delete(synchronize_session=False)
            db.query(models.Transcript).filter(models.Transcript.video_id.in_(video_ids)).delete(synchronize_session=False)
        
        # Delete videos and articles
        db.query(models.Video).filter(models.Video.topic_id == topic_id).delete()
        db.query(models.NewsArticle).filter(models.NewsArticle.topic_id == topic_id).delete()
        
        # Invalidate cache for this topic
        cache_service.invalidate_topic_cache(topic.topic_name)
        
        db.commit()
        return {"message": f"All data cleared for topic '{topic.topic_name}'"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing topic data: {str(e)}")


# CACHE MANAGEMENT ENDPOINTS
@app.get("/api/admin/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    stats = cache_service.get_cache_stats()
    return {
        "cache_stats": stats,
        "message": "In-memory cache statistics"
    }


@app.post("/api/admin/cache/clear")
async def clear_cache():
    """Clear all cache entries"""
    cache_service.clear_all_cache()
    return {"message": "All cache cleared successfully"}


@app.delete("/api/admin/cache/topic/{topic_name}")
async def invalidate_topic_cache_endpoint(topic_name: str):
    """Invalidate cache for a specific topic"""
    cache_service.invalidate_topic_cache(topic_name)
    return {"message": f"Cache invalidated for topic: {topic_name}"}


@app.post("/api/admin/cache/cleanup")
async def cleanup_expired_cache():
    """Remove expired cache entries"""
    cache = cache_service.get_cache()
    removed = cache.cleanup_expired()
    return {"message": f"Removed {removed} expired cache entries"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
