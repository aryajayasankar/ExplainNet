from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, ForeignKey, REAL
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Topic(Base):
    __tablename__ = 'topics'
    topic_id = Column(Integer, primary_key=True)
    topic_name = Column(Text, nullable=False, unique=True)

class Source(Base):
    __tablename__ = 'sources'
    source_id = Column(Integer, primary_key=True)
    source_name = Column(Text, nullable=False)
    base_url = Column(Text)
    platform = Column(String(50)) # 'News' or 'YouTube'

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

class Video(Base):
    __tablename__ = 'videos'
    video_id = Column(String(255), primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.topic_id'))
    source_id = Column(Integer, ForeignKey('sources.source_id')) # Links to the YouTube channel as a source
    title = Column(Text, nullable=False)
    url = Column(Text, unique=True)
    publication_date = Column(TIMESTAMP)
    description = Column(Text)
    view_count = Column(Integer)
    like_count = Column(Integer)
    comment_count = Column(Integer)

class Comment(Base):
    __tablename__ = 'comments'
    comment_id = Column(String(255), primary_key=True)
    video_id = Column(String(255), ForeignKey('videos.video_id'))
    topic_id = Column(Integer, ForeignKey('topics.topic_id'))
    comment_text = Column(Text)
    author_name = Column(Text)
    publication_date = Column(TIMESTAMP)
    like_count = Column(Integer)