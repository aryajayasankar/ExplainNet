import sqlite3
import shutil
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'explainnet.db')
DB_PATH = os.path.abspath(DB_PATH)
BACKUP = DB_PATH + '.backup'

print('DB path:', DB_PATH)
if not os.path.exists(DB_PATH):
    print('Database not found at', DB_PATH)
    raise SystemExit(1)

print('Backing up DB to', BACKUP)
shutil.copy2(DB_PATH, BACKUP)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Check if column exists
cur.execute("PRAGMA table_info(news_articles)")
cols = [r[1] for r in cur.fetchall()]
print('news_articles columns:', cols)
if 'overall_sentiment' in cols:
    print('overall_sentiment already present, nothing to do')
else:
    print('Adding overall_sentiment column to news_articles')
    cur.execute("ALTER TABLE news_articles ADD COLUMN overall_sentiment TEXT")
    conn.commit()
    print('Column added')

conn.close()
print('Done')
