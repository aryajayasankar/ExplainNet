"""
Migration script to add emotions_json column to sentiments and comments tables
"""
import sqlite3
import os

def migrate_add_emotions():
    # Database paths
    db_paths = [
        "backend/explainnet.db",
        "explainnet.db"
    ]
    
    for db_path in db_paths:
        if not os.path.exists(db_path):
            print(f"⏭️  Skipping {db_path} (not found)")
            continue
            
        print(f"\n📊 Migrating {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if emotions column already exists in sentiments
            cursor.execute("PRAGMA table_info(sentiments)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'emotions_json' not in columns:
                print("  ➕ Adding emotions_json column to sentiments table...")
                cursor.execute("""
                    ALTER TABLE sentiments 
                    ADD COLUMN emotions_json TEXT
                """)
                print("  ✅ Added emotions_json to sentiments")
            else:
                print("  ⏭️  emotions_json already exists in sentiments")
            
            # Check if emotions column already exists in comments
            cursor.execute("PRAGMA table_info(comments)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'gemini_emotions_json' not in columns:
                print("  ➕ Adding gemini_emotions_json column to comments table...")
                cursor.execute("""
                    ALTER TABLE comments 
                    ADD COLUMN gemini_emotions_json TEXT
                """)
                print("  ✅ Added gemini_emotions_json to comments")
            else:
                print("  ⏭️  gemini_emotions_json already exists in comments")
            
            # Also add for HuggingFace (VADER) emotions if needed
            if 'hf_emotions_json' not in columns:
                print("  ➕ Adding hf_emotions_json column to comments table...")
                cursor.execute("""
                    ALTER TABLE comments 
                    ADD COLUMN hf_emotions_json TEXT
                """)
                print("  ✅ Added hf_emotions_json to comments")
            else:
                print("  ⏭️  hf_emotions_json already exists in comments")
            
            # Add relevance_score to news_articles
            cursor.execute("PRAGMA table_info(news_articles)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'relevance_score' not in columns:
                print("  ➕ Adding relevance_score column to news_articles table...")
                cursor.execute("""
                    ALTER TABLE news_articles 
                    ADD COLUMN relevance_score INTEGER
                """)
                print("  ✅ Added relevance_score to news_articles")
            else:
                print("  ⏭️  relevance_score already exists in news_articles")
            
            conn.commit()
            print(f"✅ Successfully migrated {db_path}")
            
        except Exception as e:
            print(f"❌ Error migrating {db_path}: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    print("🔄 Starting emotions column migration...")
    migrate_add_emotions()
    print("\n✨ Migration complete!")
