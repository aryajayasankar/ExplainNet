from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime

try:
    from . import models
except ImportError:
    import models

def get_or_create_topic(db: Session, topic_name: str):
    topic = db.query(models.Topic).filter(models.Topic.topic_name == topic_name).first()
    if not topic:
        topic = models.Topic(topic_name=topic_name, search_date=datetime.utcnow())
        db.add(topic)
        db.commit()
        db.refresh(topic)
    else:
        # Update search_date when topic is analyzed again
        topic.search_date = datetime.utcnow()
        db.commit()
        db.refresh(topic)
    return topic

def get_or_create_source(db: Session, source_name: str, platform: str):
    source = db.query(models.Source).filter(models.Source.source_name == source_name).first()
    if not source:
        source = models.Source(source_name=source_name, platform=platform)
        db.add(source)
        db.commit()
        db.refresh(source)
    return source

def create_article(db: Session, article: dict, topic_id: int, source_id: int):
    # Check if article already exists (by URL)
    existing_article = db.query(models.Article).filter(models.Article.url == article['url']).first()
    if existing_article:
        # Article already exists, skip
        return existing_article
    
    db_article = models.Article(
        topic_id=topic_id, source_id=source_id,
        headline=article['headline'], url=article['url'],
        author=article.get('author'), publication_date=article.get('publication_date'),
        full_text=article.get('full_text'), data_source_api=article.get('data_source_api'),
        country=article.get('country'), language=article.get('language')
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

def create_video_with_comments(db: Session, video: dict, topic_id: int, source_id: int):
    existing = db.query(models.Video).filter(models.Video.video_id == video['video_id']).first()
    if existing:
        return existing
    
    db_video = models.Video(
        video_id=video['video_id'], topic_id=topic_id, source_id=source_id,
        title=video['title'], url=f"https://www.youtube.com/watch?v={video['video_id']}",
        publication_date=video.get('publication_date'), description=video.get('description'),
        view_count=video.get('view_count'), like_count=video.get('like_count'),
        comment_count=video.get('comment_count')
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    
    for c in video.get('comments', []):
        db.add(models.Comment(
            comment_id=c['comment_id'], 
            video_id=db_video.video_id, 
            topic_id=topic_id, 
            comment_text=c.get('comment_text'), 
            author_name=c.get('author_name'), 
            publication_date=c.get('publication_date'), 
            like_count=c.get('like_count')
        ))
    db.commit()
    return db_video

# SIMPLE VERSION - just get basic topic data
def get_topics_with_stats(db: Session):
    # First, let's just get topics without any joins to test
    topics = db.query(models.Topic).all()
    result = []
    
    for topic in topics:
        # Count articles manually
        article_count = db.query(models.Article).filter(models.Article.topic_id == topic.topic_id).count()
        # Count videos manually  
        video_count = db.query(models.Video).filter(models.Video.topic_id == topic.topic_id).count()
        
        result.append({
            "topic_id": topic.topic_id,
            "topic_name": topic.topic_name,
            "search_date": topic.search_date,
            "article_count": article_count,
            "video_count": video_count
        })
    
    return result

def get_news_reliability_for_topic(db: Session, topic_id: int):
    articles = (db.query(models.Article).options(joinedload(models.Article.source)).filter(models.Article.topic_id == topic_id, models.Article.data_source_api == 'NewsAPI.org').order_by(models.Article.publication_date.asc()).all())
    if not articles: 
        return []
    
    ranked_sources, seen_ids = [], set()
    for article in articles:
        if article.source and article.source_id not in seen_ids:
            ranked_sources.append({
                "source_id": article.source_id, 
                "source_name": article.source.source_name, 
                "publication_date": article.publication_date
            })
            seen_ids.add(article.source_id)
    
    for i, source in enumerate(ranked_sources):
        source["rank"] = i + 1
        source["speed_score"] = max(0, 100 - i * 10)
    
    return ranked_sources