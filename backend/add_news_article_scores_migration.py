import sqlite3
import shutil
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'explainnet.db')
DB_PATH = os.path.abspath(DB_PATH)
BACKUP = DB_PATH + '.backup2'

print('DB path:', DB_PATH)
if not os.path.exists(DB_PATH):
    print('Database not found at', DB_PATH)
    raise SystemExit(1)

print('Backing up DB to', BACKUP)
shutil.copy2(DB_PATH, BACKUP)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Check existing columns
cur.execute("PRAGMA table_info(news_articles)")
cols = [r[1] for r in cur.fetchall()]
print('news_articles columns before:', cols)

added = False
if 'positive_score' not in cols:
    print('Adding positive_score')
    cur.execute("ALTER TABLE news_articles ADD COLUMN positive_score REAL")
    added = True
if 'negative_score' not in cols:
    print('Adding negative_score')
    cur.execute("ALTER TABLE news_articles ADD COLUMN negative_score REAL")
    added = True
if 'neutral_score' not in cols:
    print('Adding neutral_score')
    cur.execute("ALTER TABLE news_articles ADD COLUMN neutral_score REAL")
    added = True

if added:
    conn.commit()
    print('Columns added')
else:
    print('No columns needed')

cur.execute("PRAGMA table_info(news_articles)")
cols_after = [r[1] for r in cur.fetchall()]
print('news_articles columns after:', cols_after)

conn.close()
print('Done')
