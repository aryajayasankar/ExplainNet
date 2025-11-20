import sqlite3

conn = sqlite3.connect('Z:\\ExplainNet-ARUU\\backend\\explainnet.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = [row[0] for row in cursor.fetchall()]
print("Tables in database:", tables)

if 'videos' in tables:
    cursor.execute("PRAGMA table_info(videos)")
    columns = cursor.fetchall()
    print("\nColumns in videos table:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Check if emotions_json exists
    col_names = [col[1] for col in columns]
    print(f"\n✅ emotions_json column exists: {'emotions_json' in col_names}")

conn.close()
