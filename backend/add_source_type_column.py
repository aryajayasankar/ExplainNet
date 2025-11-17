"""
Add source_type column to news_articles table
"""
import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), "explainnet.db")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if the column already exists
    cursor.execute("PRAGMA table_info(news_articles)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'source_type' not in columns:
        # Add the source_type column
        cursor.execute("ALTER TABLE news_articles ADD COLUMN source_type VARCHAR(50)")
        conn.commit()
        print("✓ Successfully added source_type column to news_articles table")
    else:
        print("✓ source_type column already exists")
        
except Exception as e:
    print(f"✗ Error: {e}")
    conn.rollback()
finally:
    conn.close()
