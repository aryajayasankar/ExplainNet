from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from . import models

def get_or_create_topic(db: Session, topic_name: str):
    topic = db.query(models.Topic).filter(models.Topic.topic_name == topic_name).first()
    if not topic:
        topic = models.Topic(topic_name=topic_name)
        db.add(topic)
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
    db_article = models.Article(
        topic_id=topic_id,
        source_id=source_id,
        headline=article['headline'],
        url=article['url'],
        author=article.get('author'),
        publication_date=article.get('publication_date'),
        full_text=article.get('full_text'),
        data_source_api=article.get('data_source_api'),
        country=article.get('country'),
        language=article.get('language')
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

def create_video_with_comments(db: Session, video: dict, topic_id: int, source_id: int):
    db_video = db.query(models.Video).filter(models.Video.video_id == video['video_id']).first()
    if db_video:
        return db_video

    db_video = models.Video(
        video_id=video['video_id'],
        topic_id=topic_id,
        source_id=source_id,
        title=video['title'],
        url=f"https://www.youtube.com/watch?v={video['video_id']}",
        publication_date=video.get('publication_date'),
        description=video.get('description'),
        view_count=video.get('view_count'),
        like_count=video.get('like_count'),
        comment_count=video.get('comment_count')
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)

    for comment in video.get('comments', []):
        db_comment = models.Comment(
            comment_id=comment['comment_id'],
            video_id=db_video.video_id,
            topic_id=topic_id,
            comment_text=comment.get('comment_text'),
            author_name=comment.get('author_name'),
            publication_date=comment.get('publication_date'),
            like_count=comment.get('like_count')
        )
        db.add(db_comment)
    
    db.commit()
    return db_video

def get_topics_with_stats(db: Session):
    results = (db.query(models.Topic, func.count(func.distinct(models.Article.article_id)).label("article_count"), func.count(func.distinct(models.Video.video_id)).label("video_count")).outerjoin(models.Article, models.Topic.topic_id == models.Article.topic_id).outerjoin(models.Video, models.Topic.topic_id == models.Video.topic_id).group_by(models.Topic.topic_id).all())
    return [{"topic_id": t.topic_id, "topic_name": t.topic_name, "article_count": ac, "video_count": vc} for t, ac, vc in results]

def get_news_reliability_for_topic(db: Session, topic_id: int):
    articles = (db.query(models.Article).options(joinedload(models.Article.source)).filter(models.Article.topic_id == topic_id, models.Article.data_source_api == 'NewsAPI.org').order_by(models.Article.publication_date.asc()).all())
    if not articles: return []
    ranked_sources, seen_ids = [], set()
    for article in articles:
        if article.source and article.source_id not in seen_ids:
            ranked_sources.append({"source_id": article.source_id, "source_name": article.source.source_name, "publication_date": article.publication_date})
            seen_ids.add(article.source_id)
    for i, source in enumerate(ranked_sources):
        source["rank"] = i + 1
        source["speed_score"] = max(0, 100 - i * 10)
    return ranked_sources