import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable not set!")

# Create engine
engine = create_engine(DATABASE_URL)

print("Connecting to database...")
with engine.connect() as conn:
    # Drop all tables manually
    print("Dropping all existing tables...")
    conn.execute(text("DROP TABLE IF EXISTS comments CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS articles CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS videos CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS sources CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS topics CASCADE;"))
    conn.commit()
    print("All tables dropped.")

# Now import and create tables
print("Creating tables with new schema...")
import sys
sys.path.append('.')

# Temporarily modify models.py import
import database
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

Base = database.Base

class Topic(Base):
    __tablename__ = 'topics'
    topic_id = Column(Integer, primary_key=True)
    topic_name = Column(Text, nullable=False, unique=True)
    search_date = Column(TIMESTAMP, default=datetime.utcnow)

class Source(Base):
    __tablename__ = 'sources'
    source_id = Column(Integer, primary_key=True)
    source_name = Column(Text, nullable=False)
    platform = Column(String(50))
    
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
    data_source_api = Column(String(50))
    country = Column(String(10))
    language = Column(String(10))
    
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
    comment_text = Column(Text, nullable=False)
    author_name = Column(Text)
    publication_date = Column(TIMESTAMP)
    like_count = Column(Integer)
    
    video = relationship("Video", back_populates="comments")

# Create all tables
Base.metadata.create_all(bind=engine)
print("All tables created successfully!")
print("Database has been cleared and recreated with search_date column.")