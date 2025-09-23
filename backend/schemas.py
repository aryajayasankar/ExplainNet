from pydantic import BaseModel

class TopicCreate(BaseModel):
    topic_name: str

class Topic(BaseModel):
    topic_id: int
    topic_name: str
    article_count: int
    video_count: int

    class Config:
        from_attributes = True