# Vosk Transcription Service

def transcribe_video(video_id: str) -> dict:
    print(f"  - Transcribing with Vosk...")
    
    try:
        from backend.transcription_engine.vosk_worker import VoskTranscriber
        
        transcriber = VoskTranscriber()
        result = transcriber.transcribe_video(video_id)
        
        if result.get("text"):
            print(f"  - ✓ Vosk: {result.get('word_count', 0)} words")
            return result
        else:
            print(f"  - ⚠️  Failed: {result.get('error', 'Unknown')}")
            
    except ImportError as e:
        print(f"  - ⚠️  Vosk import failed: {str(e)}")
        print(f"  - Ensure vosk and yt-dlp are installed: pip install vosk yt-dlp")
        
    except Exception as e:
        print(f"  - ⚠️  Error: {str(e)}")
    
    return {
        "text": "",
        "language": "en",
        "confidence": 0.0,
        "word_count": 0,
        "source": "none"
    }


