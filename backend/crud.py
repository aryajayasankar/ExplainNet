from sqlalchemy.orm import Session
import models

def get_or_create_topic(db: Session, topic_name: str):
    topic = db.query(models.Topic).filter(models.Topic.topic_name == topic_name).first()
    if not topic:
        topic = models.Topic(topic_name=topic_name)
        db.add(topic)
        db.commit()
        db.refresh(topic)
    return topic

def get_or_create_source(db: Session, source_name: str, platform: str, base_url: str = None):
    source = db.query(models.Source).filter(models.Source.source_name == source_name).first()
    if not source:
        source = models.Source(source_name=source_name, platform=platform, base_url=base_url)
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
        publication_date=article['publication_date'],
        full_text=article['full_text']
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

def create_video_with_comments(db: Session, video: dict, topic_id: int, source_id: int):
    # Check if video already exists to avoid duplicates
    db_video = db.query(models.Video).filter(models.Video.video_id == video['video_id']).first()
    if db_video:
        return db_video # Already exists, do nothing

    db_video = models.Video(
        video_id=video['video_id'],
        topic_id=topic_id,
        source_id=source_id,
        title=video['title'],
        url=f"https://www.youtube.com/watch?v={video['video_id']}",
        publication_date=video['publication_date'],
        description=video['description'],
        view_count=video.get('view_count'),
        like_count=video.get('like_count'),
        comment_count=video.get('comment_count')
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)

    # Now add comments for this video
    for comment in video.get('comments', []):
        db_comment = models.Comment(
            comment_id=comment['comment_id'],
            video_id=db_video.video_id,
            topic_id=topic_id,
            comment_text=comment['comment_text'],
            author_name=comment['author_name'],
            publication_date=comment['publication_date'],
            like_count=comment['like_count']
        )
        db.add(db_comment)

    db.commit()
    return db_video