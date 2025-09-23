from pydantic import BaseModel

class TopicCreate(BaseModel):
    topic_name: str