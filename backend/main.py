from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

import crud
import models
import schemas
import pipeline
from database import SessionLocal, engine

# This creates the tables if they don't exist
# Note: For production, you'd use a migration tool like Alembic
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/analyze/")
def analyze_topic(topic_request: schemas.TopicCreate, db: Session = Depends(get_db)):
    topic_name = topic_request.topic_name

    # 1. Get or create the topic in the DB
    topic = crud.get_or_create_topic(db, topic_name=topic_name)

    # 2. Collect data from APIs
    print("--- Starting Data Collection ---")
    news_articles = pipeline.collect_news_data(topic_name)
    youtube_videos = pipeline.collect_youtube_data(topic_name)
    print("--- Data Collection Finished ---")

    # 3. Save news data to DB
    if news_articles:
        news_source = crud.get_or_create_source(db, source_name="The Guardian", platform="News")
        for article_data in news_articles:
            # Basic check to avoid duplicates
            existing_article = db.query(models.Article).filter(models.Article.url == article_data['url']).first()
            if not existing_article:
                crud.create_article(db, article=article_data, topic_id=topic.topic_id, source_id=news_source.source_id)
        print(f"Saved {len(news_articles)} articles to DB.")

    # 4. Save YouTube data to DB
    if youtube_videos:
        for video_data in youtube_videos:
            channel_source = crud.get_or_create_source(db, source_name=video_data['channel_name'], platform="YouTube")
            crud.create_video_with_comments(db, video=video_data, topic_id=topic.topic_id, source_id=channel_source.source_id)
        print(f"Saved {len(youtube_videos)} videos and their comments to DB.")

    return {"status": "success", "message": f"Analysis complete for topic: {topic_name}"}