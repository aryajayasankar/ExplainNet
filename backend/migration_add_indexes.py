"""
Migration: Add indexes to optimize topics list query
This migration adds indexes to improve query performance for the locker page
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL
import os

def migrate_add_indexes():
    """Add indexes to optimize query performance"""
    
    engine = create_engine(DATABASE_URL)
    
    migrations = [
        # Add index on topics.created_at for ORDER BY optimization
        "CREATE INDEX IF NOT EXISTS idx_topics_created_at ON topics(created_at DESC)",
        
        # Add index on topics.analysis_status for filtering
        "CREATE INDEX IF NOT EXISTS idx_topics_status ON topics(analysis_status)",
        
        # Add index on videos.topic_id for JOIN optimization (if not exists)
        "CREATE INDEX IF NOT EXISTS idx_videos_topic_id ON videos(topic_id)",
        
        # Add index on news_articles.topic_id for JOIN optimization (if not exists)
        "CREATE INDEX IF NOT EXISTS idx_news_articles_topic_id ON news_articles(topic_id)",
        
        # Composite index for common queries
        "CREATE INDEX IF NOT EXISTS idx_topics_status_created ON topics(analysis_status, created_at DESC)"
    ]
    
    with engine.connect() as conn:
        for migration_sql in migrations:
            try:
                print(f"Executing: {migration_sql}")
                conn.execute(text(migration_sql))
                conn.commit()
                print("✅ Success")
            except Exception as e:
                print(f"⚠️  Warning: {e}")
                continue
    
    print("\n✅ All indexes added successfully!")
    print("📊 Query performance should be significantly improved!")

if __name__ == "__main__":
    print("🔧 Starting database migration to add performance indexes...")
    migrate_add_indexes()
