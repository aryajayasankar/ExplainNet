import sqlite3
import os
import sys
import uuid

# ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend import database, crud

# Ensure stdout encoding on Windows consoles
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


def run():
    db = database.SessionLocal()

    # Create a unique topic
    topic_name = f"persist-test-{uuid.uuid4().hex[:8]}"
    topic = crud.create_topic(db, type('T', (), {'topic_name': topic_name}))
    print('Created topic id=', topic.id)

    # Create a unique video
    vid = f"persist_vid_{uuid.uuid4().hex[:8]}"
    video_data = {
        'video_id': vid,
        'title': 'Persist Test Video',
        'channel_id': 'persist_chan_1',
        'channel_name': 'Persist Channel',
        'view_count': 1234,
        'like_count': 12,
        'comment_count': 3,
        'duration': 'PT2M'
    }
    db_video = crud.create_video(db, video_data, topic.id)
    print('Created video id=', db_video.id, 'video_id=', vid)

    # Insert a transcript row that would normally be analyzed
    transcript_data = {
        'text': 'I find this content informative and useful. No sarcasm intended.',
        'language': 'en',
        'confidence': 0.95,
        'word_count': 9,
        'processing_time': 0.2,
        'status': 'success'
    }
    crud.create_transcript(db, transcript_data, db_video.id)
    print('Inserted transcript')

    # Mocked model outputs (deterministic)
    hf_out = {
        'model_name': 'huggingface_local',
        'sentiment': 'POSITIVE',
        'confidence': 0.92,
        'positive_score': 0.92,
        'negative_score': 0.01,
        'neutral_score': 0.07,
        'justification': 'HF: high positivity due to words like "informative" and "useful"'
    }

    gem_out = {
        'model_name': 'gemini',
        'sentiment': 'POSITIVE',
        'confidence': 0.85,
        'positive_score': 0.85,
        'negative_score': 0.0,
        'neutral_score': 0.15,
        'justification': 'Gemini: positive tone, no sarcasm detected',
        'sarcasm_score': 0.02
    }

    # Persist both sentiments via CRUD (this is what pipeline would do)
    s1 = crud.create_sentiment(db, hf_out, db_video.id)
    s2 = crud.create_sentiment(db, gem_out, db_video.id)
    print('Persisted sentiments IDs:', s1.id, s2.id)

    # Read back and display key fields to verify justifications persisted
    rows = crud.get_sentiments_by_video(db, db_video.id)
    for r in rows:
        print('---')
        print('id:', r.id)
        print('model_name:', r.model_name)
        print('sentiment:', r.sentiment)
        print('confidence:', r.confidence)
        # these attributes may exist depending on migration
        print('hf_justification:', getattr(r, 'hf_justification', None))
        print('gemini_justification:', getattr(r, 'gemini_justification', None))
        print('gemini_sarcasm_score:', getattr(r, 'gemini_sarcasm_score', None))

    db.close()


if __name__ == '__main__':
    run()
