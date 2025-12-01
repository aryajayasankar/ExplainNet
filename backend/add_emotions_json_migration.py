"""
Migration: Add emotions_json column to videos table
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "explainnet.db")

def migrate():
    print("=" * 80)
    print("Database Migration: Add emotions_json column to videos table")
    print("=" * 80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(videos)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "emotions_json" not in columns:
            print("Adding 'emotions_json' column to videos table...")
            cursor.execute("ALTER TABLE videos ADD COLUMN emotions_json TEXT")
            conn.commit()
            print("✓ Successfully added 'emotions_json' column!")
        else:
            print("✓ Column 'emotions_json' already exists")
        
        # Verify
        cursor.execute("PRAGMA table_info(videos)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "emotions_json" in columns:
            print("✓ Migration verified successfully!")
        else:
            print("❌ Migration verification failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("=" * 80)

if __name__ == "__main__":
    migrate()
