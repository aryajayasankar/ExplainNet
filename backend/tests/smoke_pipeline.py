import asyncio
import json
import sys
import os

# Ensure stdout uses UTF-8 encoding so emoji/Unicode prints don't fail on Windows consoles
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
from sqlalchemy.orm import Session

# Ensure project root is on sys.path so `import backend` works when running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend import database, crud, pipeline

# This smoke test will create a fake video entry and run process_video with mocked data.
# It avoids external API calls by providing video_data similar to youtube_service.get_video_details output.

async def run_smoke():
    # Create DB session
    db_session = database.SessionLocal()

    # Create a fake topic for the test (unique name to avoid clashes)
    import uuid
    topic_name = f"smoke-test-topic-{uuid.uuid4().hex[:8]}"
    topic = crud.create_topic(db_session, type('T', (), {'topic_name': topic_name}))
    print('Created test topic id=', topic.id)

    # Prepare fake video data (minimal required fields used by process_video)
    import uuid as _uuid
    vid_id = f"smoke_test_vid_{_uuid.uuid4().hex[:8]}"

    video_data = {
        'video_id': vid_id,
        'title': 'Smoke Test Video',
        'channel_id': 'smoke_channel_1',
        'channel_name': 'Smoke Channel',
        'view_count': 1000,
        'like_count': 50,
        'comment_count': 2,
        'duration': 'PT5M',
        'published_at': None,
        'is_valid': True,
        # Provide a transcript by patching transcription_service at runtime is harder; instead we'll
        # call pipeline.process_video and then insert a transcript record so process_video sees it.
    }

    # Insert the video record (pipeline normally does this internally)
    db_video = crud.create_video(db_session, {k:v for k,v in video_data.items() if k!='is_valid'}, topic.id)
    print('Created video id=', db_video.id)

    # Create a transcript record so process_video will analyze it
    transcript_data = {
        'text': 'This is a positive test transcript. We like this content and it is great.',
        'language': 'en',
        'confidence': 0.98,
        'word_count': 9,
        'processing_time': 0.5,
        'status': 'success'
    }
    crud.create_transcript(db_session, transcript_data, db_video.id)
    print('Inserted transcript')

    # Monkeypatch huggingface_service and gemini_service to return deterministic outputs
    from backend import huggingface_service, gemini_service

    async def hf_dummy(text):
        return {
            'model_name': 'huggingface_local',
            'sentiment': 'POSITIVE',
            'confidence': 0.9,
            'positive_score': 0.9,
            'negative_score': 0.0,
            'neutral_score': 0.1,
            'justification': 'Test HF justification'
        }

    async def gemini_dummy(text, title=''):
        return {
            'model_name': 'gemini',
            'sentiment': 'POSITIVE',
            'confidence': 0.8,
            'positive_score': 0.8,
            'negative_score': 0.0,
            'neutral_score': 0.2,
            'justification': 'Test Gemini justification',
            'sarcasm_score': 0.0
        }

    huggingface_service.analyze_sentiment = hf_dummy
    gemini_service.analyze_sentiment_advanced = gemini_dummy
    gemini_service.extract_entities = lambda text, context='': {'persons': [], 'organizations': [], 'locations': [], 'products': [], 'events': [], 'other': []}

    # Now call process_video directly (it will read the transcript which we created)
    try:
        await pipeline.process_video(db_session, topic.id, video_data)
        print('process_video completed')
    except Exception as e:
        print('process_video error:', e)

    # Fetch saved sentiments and print them
    sentiments = crud.get_sentiments_by_video(db_session, db_video.id)
    print('Saved sentiments:', [ (s.model_name, s.sentiment, s.hf_justification if hasattr(s, 'hf_justification') else None, s.gemini_justification if hasattr(s, 'gemini_justification') else None) for s in sentiments ])

    # Cleanup (optional)
    # crud.delete_topic(db_session, topic.id)
    db_session.close()

if __name__ == '__main__':
    asyncio.run(run_smoke())
