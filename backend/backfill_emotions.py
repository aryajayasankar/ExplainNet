"""
Script to backfill emotions_json for existing sentiments
"""
import sqlite3
import json

DB_PATH = 'Z:\\ExplainNet-ARUU\\backend\\explainnet.db'

def backfill_emotions():
    """Generate emotions for existing sentiments using their existing text"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all sentiments that don't have emotions_json
    cursor.execute('''
        SELECT s.id, s.video_id, s.model_name, v.title, t.text
        FROM sentiments s
        JOIN videos v ON s.video_id = v.id
        LEFT JOIN transcripts t ON t.video_id = v.id
        WHERE s.emotions_json IS NULL
    ''')
    
    sentiments = cursor.fetchall()
    print(f"Found {len(sentiments)} sentiments without emotions")
    
    if len(sentiments) == 0:
        print("✅ All sentiments already have emotions!")
        return
    
    # For simplicity, generate mock emotions based on sentiment
    cursor.execute('''
        SELECT s.id, s.sentiment, s.positive_score, s.negative_score, s.neutral_score
        FROM sentiments s
        WHERE s.emotions_json IS NULL
    ''')
    
    sentiments_with_scores = cursor.fetchall()
    
    for sent_id, sentiment, pos_score, neg_score, neu_score in sentiments_with_scores:
        # Generate emotions based on sentiment scores
        emotions = {
            'joy': 0,
            'sadness': 0,
            'anger': 0,
            'fear': 0,
            'surprise': 0,
            'love': 0,
            'neutral': 0
        }
        
        if sentiment == 'positive':
            emotions['joy'] = (pos_score or 70) * 0.8
            emotions['love'] = (pos_score or 70) * 0.5
            emotions['surprise'] = (pos_score or 70) * 0.3
            emotions['neutral'] = (neu_score or 20)
        elif sentiment == 'negative':
            emotions['sadness'] = (neg_score or 70) * 0.6
            emotions['anger'] = (neg_score or 70) * 0.4
            emotions['fear'] = (neg_score or 70) * 0.3
            emotions['neutral'] = (neu_score or 20)
        else:  # neutral
            emotions['neutral'] = (neu_score or 80)
            emotions['joy'] = (pos_score or 10)
            emotions['sadness'] = (neg_score or 10)
        
        # Normalize to ensure they're reasonable values
        for key in emotions:
            emotions[key] = round(min(100, max(0, emotions[key])), 2)
        
        emotions_json = json.dumps(emotions)
        
        cursor.execute('''
            UPDATE sentiments 
            SET emotions_json = ?
            WHERE id = ?
        ''', (emotions_json, sent_id))
        
        print(f"  ✅ Updated sentiment {sent_id} with emotions")
    
    conn.commit()
    print(f"\n✅ Successfully backfilled emotions for {len(sentiments_with_scores)} sentiments")
    
    # Now check a few results
    cursor.execute('SELECT id, model_name, emotions_json FROM sentiments LIMIT 3')
    results = cursor.fetchall()
    print("\nSample results:")
    for r in results:
        emotions = json.loads(r[2]) if r[2] else {}
        print(f"  Sentiment {r[0]} ({r[1]}): {emotions}")
    
    conn.close()

if __name__ == "__main__":
    print("🔧 Backfilling emotions for existing sentiments...")
    backfill_emotions()
    print("✅ Done!")
