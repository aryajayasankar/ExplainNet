"""
Clear all topics from the database.
This script will delete all topics and their associated videos, articles, sentiments, etc.
due to cascade delete relationships.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SessionLocal
from backend.models import Topic

def clear_all_topics():
    db = SessionLocal()
    try:
        # Get count before deletion
        count = db.query(Topic).count()
        print(f"Found {count} topic(s) in the database.")
        
        if count == 0:
            print("Database is already empty.")
            return
        
        # Delete all topics (cascade will handle related records)
        deleted = db.query(Topic).delete()
        db.commit()
        
        print(f"✅ Successfully deleted {deleted} topic(s) and all related data.")
        print("Database is now clear and ready for new topics.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_topics()
