from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
from typing import List, Dict
import asyncio
from database import engine, Base, get_db
import models
import schemas
import crud
import pipeline
import cache_service
import gemini_service

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


@app.get("/api/topics/create-streaming")
async def create_topic_streaming(
    topic: str,
    db: Session = Depends(get_db)
):
    """Create a new topic and stream analysis progress via SSE"""
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    topic_id = None
    
    async def event_stream():
        nonlocal topic_id
        try:
            # Step 1: Create topic in database
            yield f"data: {json.dumps({'status': 'progress', 'message': '📝 Creating topic...', 'type': 'info'})}\n\n"
            await asyncio.sleep(0.2)
            
            db_topic = crud.create_topic(db, schemas.TopicCreate(topic_name=topic))
            topic_id = db_topic.id
            
            yield f"data: {json.dumps({'status': 'progress', 'message': f'✅ Topic created: {topic}', 'type': 'success', 'topic_id': topic_id})}\n\n"
            await asyncio.sleep(0.2)
            
            # Step 2: Search YouTube
            yield f"data: {json.dumps({'status': 'progress', 'message': f'🔍 Searching YouTube for \"{topic}\"...', 'type': 'info'})}\n\n"
            await asyncio.sleep(0.3)
            
            # Stream progress from pipeline
            async for progress_data in pipeline.analyze_topic_streaming(db, topic_id, topic):
                yield f"data: {json.dumps(progress_data)}\n\n"
                await asyncio.sleep(0.1)
            
            # Final completion message
            yield f"data: {json.dumps({'status': 'complete', 'topic_id': topic_id, 'message': '🎉 Analysis complete!', 'type': 'success'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': f'❌ Error: {str(e)}', 'type': 'error'})}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/topics", response_model=List[schemas.TopicResponse])
async def get_topics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all topics with caching"""
    # Create cache key based on skip and limit
    cache_key = f"topics_list_{skip}_{limit}"
    
    # Try to get from cache first (30 second TTL for fast updates)
    cached = cache_service.get_cached(cache_key)
    if cached is not None:
        return cached
    
    # If not cached, fetch from database
    topics = crud.get_topics(db, skip=skip, limit=limit)
    
    # Cache the result for 30 seconds
    cache_service.set_cached(cache_key, topics, ttl=30)
    
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


@app.patch("/api/topics/{topic_id}", response_model=schemas.TopicResponse)
async def update_topic(topic_id: int, update_data: dict, db: Session = Depends(get_db)):
    """Update a topic (e.g., processing time)"""
    topic = crud.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Update allowed fields
    if 'processing_time_seconds' in update_data:
        topic.processing_time_seconds = update_data['processing_time_seconds']
    
    db.commit()
    db.refresh(topic)
    return topic


# VIDEO ENDPOINTS
@app.get("/api/topics/{topic_id}/videos", response_model=List[schemas.VideoResponse])
async def get_topic_videos(topic_id: int, db: Session = Depends(get_db)):
    """Get all videos for a topic"""
    videos = crud.get_videos_by_topic(db, topic_id)
    print(f"📹 Returning {len(videos)} videos for topic {topic_id}")
    if videos:
        print(f"📹 First video emotions: {getattr(videos[0], 'emotions', None) or getattr(videos[0], 'emotions_json', None)}")
    
    # Convert to response models and ensure emotions are set
    response_videos = []
    for video in videos:
        video_dict = {
            "id": video.id,
            "topic_id": video.topic_id,
            "video_id": video.video_id,
            "title": video.title,
            "channel_name": video.channel_name,
            "channel_id": video.channel_id,
            "thumbnail_url": video.thumbnail_url,
            "published_at": video.published_at,
            "view_count": video.view_count,
            "like_count": video.like_count,
            "comment_count": video.comment_count,
            "duration": video.duration,
            "impact_score": video.impact_score,
            "reach_score": video.reach_score,
            "engagement_score": video.engagement_score,
            "sentiment_score": video.sentiment_score,
            "quality_score": video.quality_score,
            "influence_score": video.influence_score,
            "recency_boost": video.recency_boost,
            "overall_sentiment": video.overall_sentiment,
            "emotions_json": getattr(video, 'emotions_json', None),
            "emotions": getattr(video, 'emotions', None) or getattr(video, 'emotions_json', None)
        }
        response_videos.append(schemas.VideoResponse(**video_dict))
    
    return response_videos


@app.get("/api/topics/{topic_id}/videos/gnn")
async def get_videos_gnn(topic_id: int, db: Session = Depends(get_db)):
    """Get GNN (Graph Neural Network) data for videos - nodes and connections"""
    import math
    
    videos = crud.get_videos_by_topic(db, topic_id)
    
    # Sort by impact score and take top 12
    sorted_videos = sorted(videos, key=lambda v: v.impact_score or 0, reverse=True)[:12]
    
    if not sorted_videos:
        return {"nodes": [], "edges": []}
    
    # Calculate node positions in circular layout
    center_x = 300
    center_y = 250
    radius = 180
    
    max_impact = max([v.impact_score or 0 for v in sorted_videos])
    
    nodes = []
    for i, video in enumerate(sorted_videos):
        angle = (i * 2 * math.pi) / len(sorted_videos) - (math.pi / 2)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        # Node size based on impact score
        size = 15 + ((video.impact_score or 0) / max_impact * 25) if max_impact > 0 else 20
        
        nodes.append({
            "id": video.id,
            "video_id": video.video_id,
            "title": video.title,
            "x": round(x, 2),
            "y": round(y, 2),
            "size": round(size, 2),
            "sentiment": video.overall_sentiment or "neutral",
            "impactScore": round(video.impact_score or 0, 2)
        })
    
    # Calculate edges (connections between videos)
    edges = []
    for i, video1 in enumerate(sorted_videos):
        connections = []
        for j, video2 in enumerate(sorted_videos):
            if i >= j:  # Skip self and already processed pairs
                continue
            
            # Connect if same sentiment or similar impact (within 20%)
            same_sentiment = video1.overall_sentiment == video2.overall_sentiment
            impact1 = video1.impact_score or 0
            impact2 = video2.impact_score or 0
            
            if max(impact1, impact2) > 0:
                impact_diff = abs(impact1 - impact2) / max(impact1, impact2)
                similar_impact = impact_diff < 0.2
            else:
                similar_impact = False
            
            if same_sentiment or similar_impact:
                connections.append(video2.id)
                edges.append({
                    "source": video1.id,
                    "target": video2.id,
                    "reason": "same_sentiment" if same_sentiment else "similar_impact"
                })
        
        # Update node with connection count
        nodes[i]["connections"] = len(connections)
    
    return {
        "nodes": nodes,
        "edges": edges,
        "layout": {
            "centerX": center_x,
            "centerY": center_y,
            "radius": radius
        }
    }


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
    
    # Check if transcript exists
    if not video.transcript:
        # Provide helpful error message based on transcription status
        if video.transcription_status == 'failed':
            raise HTTPException(
                status_code=404, 
                detail=f"Transcription failed: {video.transcription_error or 'Unknown error'}"
            )
        elif video.transcription_status == 'timeout':
            raise HTTPException(
                status_code=404, 
                detail="Transcription timed out (video too long or processing issue)"
            )
        elif video.transcription_status == 'pending':
            raise HTTPException(
                status_code=404, 
                detail="Transcription pending (analysis may still be running)"
            )
        else:
            raise HTTPException(status_code=404, detail="Transcript not available")
    
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
                "relevance_score": a.relevance_score,
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
async def get_ai_synthesis(topic_id: int, force_refresh: bool = False, db: Session = Depends(get_db)):
    """
    Generate comprehensive AI synthesis combining all analytics data using Gemini.
    Returns executive summary, key trends, surprising findings, and recommendations.
    
    Args:
        topic_id: ID of the topic
        force_refresh: If True, bypass cache and regenerate analysis
        db: Database session
    
    Caching Strategy:
        - Cache is stored in database (topic.ai_synthesis_cache)
        - Cache expires after 24 hours
        - Cache auto-invalidates when videos/articles are added
        - Manual refresh via force_refresh parameter
    """
    topic = crud.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Check if we have valid cached data
    if not force_refresh and topic.ai_synthesis_cache and topic.ai_synthesis_generated_at:
        from datetime import datetime, timedelta
        import json
        
        # Check if cache is less than 24 hours old
        cache_age = datetime.utcnow() - topic.ai_synthesis_generated_at
        if cache_age < timedelta(hours=24):
            try:
                cached_synthesis = json.loads(topic.ai_synthesis_cache)
                cached_synthesis["from_cache"] = True
                cached_synthesis["cache_generated_at"] = topic.ai_synthesis_generated_at.isoformat()
                cached_synthesis["cache_age_hours"] = round(cache_age.total_seconds() / 3600, 2)
                return cached_synthesis
            except json.JSONDecodeError:
                # Invalid cache, proceed to regenerate
                pass
    
    # Cache miss or force refresh - generate new synthesis
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
    synthesis = await gemini_service.generate_ai_synthesis(topic_data)
    
    # Store in cache
    import json
    from datetime import datetime
    
    topic.ai_synthesis_cache = json.dumps(synthesis)
    topic.ai_synthesis_generated_at = datetime.utcnow()
    db.commit()
    
    synthesis["from_cache"] = False
    synthesis["cache_generated_at"] = topic.ai_synthesis_generated_at.isoformat()
    
    return synthesis


@app.get("/api/topics/{topic_id}/ai-analytics")
async def get_ai_analytics(topic_id: int, db: Session = Depends(get_db)):
    """
    Get AI analytics data for Model Agreement and Confidence Distribution charts
    """
    videos = crud.get_videos_by_topic(db, topic_id)
    
    model_agreement = {
        "both_agree": {"positive": 0, "negative": 0, "neutral": 0},
        "disagree": 0,
        "vader_only": 0,
        "gemini_only": 0,
        "no_sentiment": 0
    }
    
    confidence_data = {
        "vader": [],
        "gemini": []
    }
    
    for video in videos:
        sentiments = db.query(models.Sentiment).filter(models.Sentiment.video_id == video.id).all()
        
        vader_sentiment = None
        gemini_sentiment = None
        vader_confidence = None
        gemini_confidence = None
        
        for sent in sentiments:
            if sent.model_name in ["vader", "huggingface"]:
                vader_sentiment = sent.sentiment
                vader_confidence = sent.confidence
            elif sent.model_name == "gemini":
                gemini_sentiment = sent.sentiment
                gemini_confidence = sent.confidence
        
        # Model agreement logic
        if vader_sentiment and gemini_sentiment:
            if vader_sentiment == gemini_sentiment:
                # Both agree on same sentiment
                sentiment_key = vader_sentiment.lower() if vader_sentiment else "neutral"
                if sentiment_key in ["positive", "negative", "neutral"]:
                    model_agreement["both_agree"][sentiment_key] += 1
            else:
                model_agreement["disagree"] += 1
        elif vader_sentiment and not gemini_sentiment:
            model_agreement["vader_only"] += 1
        elif gemini_sentiment and not vader_sentiment:
            model_agreement["gemini_only"] += 1
        else:
            model_agreement["no_sentiment"] += 1
        
        # Confidence distribution
        if vader_confidence is not None:
            confidence_data["vader"].append(round(vader_confidence * 100, 1))
        if gemini_confidence is not None:
            confidence_data["gemini"].append(round(gemini_confidence * 100, 1))
    
    # Calculate agreement statistics
    total_videos = len(videos)
    total_agree = sum(model_agreement["both_agree"].values())
    
    result = {
        "total_videos": total_videos,
        "model_agreement": model_agreement,
        "agreement_percentage": round((total_agree / total_videos * 100) if total_videos > 0 else 0, 1),
        "disagreement_percentage": round((model_agreement["disagree"] / total_videos * 100) if total_videos > 0 else 0, 1),
        "confidence_data": confidence_data,
        "vader_avg_confidence": round(sum(confidence_data["vader"]) / len(confidence_data["vader"]), 1) if confidence_data["vader"] else 0,
        "gemini_avg_confidence": round(sum(confidence_data["gemini"]) / len(confidence_data["gemini"]), 1) if confidence_data["gemini"] else 0
    }
    
    return result


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
