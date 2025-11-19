import sqlite3
import json

conn = sqlite3.connect('Z:\\ExplainNet-ARUU\\backend\\explainnet.db')
cursor = conn.cursor()

# Check videos
cursor.execute('SELECT COUNT(*) FROM videos')
video_count = cursor.fetchone()[0]
print(f"Total videos: {video_count}")

# Check sentiments
cursor.execute('SELECT COUNT(*) FROM sentiments')
sentiment_count = cursor.fetchone()[0]
print(f"Total sentiments: {sentiment_count}")

# Check if sentiments have emotions_json
cursor.execute('SELECT id, video_id, model_name, emotions_json FROM sentiments LIMIT 5')
sentiments = cursor.fetchall()
print(f"\nFirst 5 sentiments:")
for s in sentiments:
    print(f"  Sentiment ID {s[0]}, Video ID {s[1]}, Model: {s[2]}")
    if s[3]:
        try:
            emotions = json.loads(s[3])
            print(f"    Emotions: {emotions}")
        except:
            print(f"    Raw emotions_json: {s[3]}")
    else:
        print(f"    ⚠️ No emotions_json")

# Check videos emotions_json
cursor.execute('SELECT id, title, emotions_json FROM videos LIMIT 3')
videos = cursor.fetchall()
print(f"\nFirst 3 videos:")
for v in videos:
    print(f"  Video ID {v[0]}: {v[1][:50]}...")
    if v[2]:
        print(f"    Has emotions_json: {v[2]}")
    else:
        print(f"    ⚠️ No emotions_json")

conn.close()
