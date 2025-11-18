"""
Migration: Add AI Synthesis Cache to Topics Table
Adds ai_synthesis_cache and ai_synthesis_generated_at columns for caching Gemini analysis results
"""
import sqlite3
from pathlib import Path

def run_migration():
    # Connect to database
    db_path = Path(__file__).parent / "explainnet.db"
    
    if not db_path.exists():
        print(f"⚠️  Database not found at {db_path}")
        print("Migration skipped - database will be created with new schema on first run")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 Starting AI Synthesis Cache Migration...")
    print("=" * 60)
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(topics)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    migrations_needed = []
    if "ai_synthesis_cache" not in existing_columns:
        migrations_needed.append(("ai_synthesis_cache", "TEXT"))
    if "ai_synthesis_generated_at" not in existing_columns:
        migrations_needed.append(("ai_synthesis_generated_at", "DATETIME"))
    
    if not migrations_needed:
        print("✅ Columns already exist. No migration needed!")
        conn.close()
        return
    
    # Add new columns
    for column_name, column_type in migrations_needed:
        try:
            alter_query = f"ALTER TABLE topics ADD COLUMN {column_name} {column_type}"
            print(f"📝 Adding column: {column_name} ({column_type})")
            cursor.execute(alter_query)
            print(f"   ✅ Successfully added {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"   ⚠️  Column {column_name} already exists, skipping")
            else:
                print(f"   ❌ Error adding {column_name}: {e}")
                conn.rollback()
                conn.close()
                raise
    
    conn.commit()
    
    # Verify migration
    cursor.execute("PRAGMA table_info(topics)")
    columns_after = [row[1] for row in cursor.fetchall()]
    
    print("\n" + "=" * 60)
    print("✅ Migration completed successfully!")
    print(f"📊 Topics table now has {len(columns_after)} columns")
    print("\n🎯 New caching columns added:")
    print("   • ai_synthesis_cache (TEXT) - Stores JSON of AI analysis")
    print("   • ai_synthesis_generated_at (DATETIME) - Timestamp of last generation")
    print("\n💡 AI Insights will now be cached in the database!")
    print("   Cache will invalidate when new videos/articles are added.")
    
    conn.close()

if __name__ == "__main__":
    run_migration()
