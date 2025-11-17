import sqlite3
import shutil
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'explainnet.db')
DB_PATH = os.path.abspath(DB_PATH)
BACKUP = DB_PATH + '.backup3'

print('DB path:', DB_PATH)
if not os.path.exists(DB_PATH):
    print('Database not found at', DB_PATH)
    raise SystemExit(1)

print('Backing up DB to', BACKUP)
shutil.copy2(DB_PATH, BACKUP)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("PRAGMA table_info(news_articles)")
cols = [r[1] for r in cur.fetchall()]
print('news_articles columns before:', cols)

if 'entities' not in cols:
    print('Adding entities column')
    cur.execute("ALTER TABLE news_articles ADD COLUMN entities TEXT")
    conn.commit()
    print('entities column added')
else:
    print('entities column already present')

cur.execute("PRAGMA table_info(news_articles)")
print('news_articles columns after:', [r[1] for r in cur.fetchall()])
conn.close()
print('Done')
