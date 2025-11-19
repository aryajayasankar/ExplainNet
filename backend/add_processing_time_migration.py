"""
Migration script to add processing_time_seconds column to topics table.
Run this script to update the database schema.
"""
import sqlite3
import os

def run_migration():
    # Get the database path (same directory as this script)
    db_path = os.path.join(os.path.dirname(__file__), 'explainnet.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(topics)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'processing_time_seconds' in columns:
            print("✓ Column 'processing_time_seconds' already exists. No migration needed.")
            return
        
        # Add the new column
        print("Adding 'processing_time_seconds' column to topics table...")
        cursor.execute("""
            ALTER TABLE topics 
            ADD COLUMN processing_time_seconds INTEGER
        """)
        
        conn.commit()
        print("✓ Successfully added 'processing_time_seconds' column!")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(topics)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'processing_time_seconds' in columns:
            print("✓ Migration verified successfully!")
        else:
            print("⚠️  Warning: Column may not have been added correctly.")
            
    except sqlite3.Error as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add processing_time_seconds column")
    print("=" * 60)
    run_migration()
    print("=" * 60)
