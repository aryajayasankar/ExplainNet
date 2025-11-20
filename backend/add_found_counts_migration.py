"""
Migration script to add videos_found and articles_found columns to topics table.
This distinguishes between search results (found) and successfully analyzed items.
"""

from sqlalchemy import create_engine, Column, Integer, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./explainnet.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def migrate():
    """Add videos_found and articles_found columns to topics table"""
    db = SessionLocal()
    try:
        print("🔄 Starting migration: Adding videos_found and articles_found columns...")
        
        # Check if columns already exist
        result = db.execute(text("PRAGMA table_info(topics)"))
        columns = [row[1] for row in result.fetchall()]
        
        # Add videos_found column if it doesn't exist
        if 'videos_found' not in columns:
            print("  ➕ Adding videos_found column...")
            db.execute(text("""
                ALTER TABLE topics 
                ADD COLUMN videos_found INTEGER DEFAULT 0
            """))
            db.commit()
            print("  ✅ videos_found column added")
        else:
            print("  ℹ️  videos_found column already exists")
        
        # Add articles_found column if it doesn't exist
        if 'articles_found' not in columns:
            print("  ➕ Adding articles_found column...")
            db.execute(text("""
                ALTER TABLE topics 
                ADD COLUMN articles_found INTEGER DEFAULT 0
            """))
            db.commit()
            print("  ✅ articles_found column added")
        else:
            print("  ℹ️  articles_found column already exists")
        
        # Migrate existing data: copy total_videos/total_articles to videos_found/articles_found
        # since old data didn't distinguish between found and analyzed
        print("  🔄 Migrating existing data...")
        db.execute(text("""
            UPDATE topics 
            SET videos_found = total_videos,
                articles_found = total_articles
            WHERE videos_found = 0 OR articles_found = 0
        """))
        db.commit()
        print("  ✅ Existing data migrated")
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
