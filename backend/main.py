from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from . import crud, models, schemas, pipeline, database

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