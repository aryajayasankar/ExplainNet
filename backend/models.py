from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base  # Import Base from database.py instead of creating a new one

class Topic(Base):
    __tablename__ = 'topics'
    topic_id = Column(Integer, primary_key=True)
    topic_name = Column(Text, nullable=False, unique=True)

class Source(Base):
    __tablename__ = 'sources'
    source_id = Column(Integer, primary_key=True)
    source_name = Column(Text, nullable=False)
    platform = Column(String(50)) # 'News' or 'YouTube'
    
    articles = relationship("Article", back_populates="source")
    videos = relationship("Video", back_populates="source")

class Article(Base):
    __tablename__ = 'articles'
    article_id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.topic_id'))
    source_id = Column(Integer, ForeignKey('sources.source_id'))
    headline = Column(Text, nullable=False)
    url = Column(Text, unique=True)
    author = Column(Text)
    publication_date = Column(TIMESTAMP)
    full_text = Column(Text)
    data_source_api = Column(String(50)) # e.g., 'Guardian' or 'NewsAPI.org'
    country = Column(String(10)) # e.g., 'US', 'IN'
    language = Column(String(10)) # e.g., 'en', 'hi'
    
    source = relationship("Source", back_populates="articles")

class Video(Base):
    __tablename__ = 'videos'
    video_id = Column(String(255), primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.topic_id'))
    source_id = Column(Integer, ForeignKey('sources.source_id'))
    title = Column(Text, nullable=False)
    url = Column(Text, unique=True)
    publication_date = Column(TIMESTAMP)
    description = Column(Text)
    view_count = Column(Integer)
    like_count = Column(Integer)
    comment_count = Column(Integer)

    source = relationship("Source", back_populates="videos")
    comments = relationship("Comment", back_populates="video")

class Comment(Base):
    __tablename__ = 'comments'
    comment_id = Column(String(255), primary_key=True)
    video_id = Column(String(255), ForeignKey('videos.video_id'))
    topic_id = Column(Integer, ForeignKey('topics.topic_id'))
    comment_text = Column(Text)
    author_name = Column(Text)
    publication_date = Column(TIMESTAMP)
    like_count = Column(Integer)

    video = relationship("Video", back_populates="comments")