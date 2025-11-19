"""
Migration script to add emotions_json column to videos table
"""
import sqlite3
import os

# Path to your database - use absolute path
DB_PATH = r"Z:\ExplainNet-ARUU\backend\explainnet.db"

def add_emotions_column():
    """Add emotions_json column to videos table"""
    print(f"Database path: {DB_PATH}")
    print(f"Database exists: {os.path.exists(DB_PATH)}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if videos table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
        if not cursor.fetchone():
            print("❌ Videos table does not exist!")
            return
            
        # Check if column already exists
        cursor.execute("PRAGMA table_info(videos)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Existing columns: {columns}")
        
        if 'emotions_json' not in columns:
            print("Adding emotions_json column to videos table...")
            cursor.execute("""
                ALTER TABLE videos 
                ADD COLUMN emotions_json TEXT
            """)
            conn.commit()
            print("✅ Successfully added emotions_json column")
        else:
            print("ℹ️  emotions_json column already exists")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Running Video Emotions Migration...")
    add_emotions_column()
    print("✅ Migration complete!")
