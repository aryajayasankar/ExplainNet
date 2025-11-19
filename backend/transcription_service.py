# Hybrid Transcription Service: YouTube Captions (Fast) + Vosk Fallback (Slow)

def transcribe_video(video_id: str, log_callback=None) -> dict:
    """
    Hybrid transcription approach:
    1. Try YouTube auto-generated captions first (< 1 second) ⚡
    2. Fall back to Vosk if no captions available (5 minutes) 🐌
    3. Return error if both fail
    
    Args:
        video_id: YouTube video ID
        log_callback: Optional callable(message: str) to send progress logs
    
    Returns:
        dict with keys: text, language, confidence, word_count, source, status
    """
    
    def log(message: str):
        """Helper to log both to console and callback"""
        print(message)
        if log_callback:
            log_callback(message)
    
    # STEP 1: Try YouTube captions first (FAST - 95% success rate)
    log("[TRANSCRIPTION_START]")
    log("[TRANSCRIPTION_LOG] Trying YouTube captions (fast method)...")
    youtube_result = transcribe_with_youtube_captions(video_id)
    
    if youtube_result.get("status") == "success" and youtube_result.get("text"):
        log(f"[TRANSCRIPTION_LOG] ✓ YouTube Captions: {youtube_result.get('word_count', 0)} words")
        log("[TRANSCRIPTION_END]")
        return youtube_result
    else:
        log("[TRANSCRIPTION_LOG] ⚠️  No YouTube captions available")
    
    # STEP 2: Fall back to Vosk transcription (SLOW - last resort)
    log("[TRANSCRIPTION_LOG] Falling back to Vosk transcription...")
    vosk_result = transcribe_with_vosk(video_id, log_callback=log_callback)
    
    if vosk_result.get("status") == "success" and vosk_result.get("text"):
        log(f"[TRANSCRIPTION_LOG] ✓ Vosk: {vosk_result.get('word_count', 0)} words")
        log("[TRANSCRIPTION_END]")
        return vosk_result
    else:
        log(f"[TRANSCRIPTION_LOG] ⚠️  Vosk failed: {vosk_result.get('error', 'Unknown')}")
    
    # STEP 3: Both methods failed
    log("[TRANSCRIPTION_LOG] ❌ All transcription methods failed")
    log("[TRANSCRIPTION_END]")
    return {
        "status": "failed",
        "text": None,
        "language": "unknown",
        "confidence": 0.0,
        "word_count": 0,
        "source": "none",
        "error": "No captions available and Vosk transcription failed"
    }


def transcribe_with_youtube_captions(video_id: str) -> dict:
    """
    Download and parse YouTube auto-generated captions (FAST METHOD)
    
    Speed: < 1 second
    Accuracy: Very high (YouTube's AI)
    Success Rate: ~95% of videos
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            TranscriptsDisabled, 
            NoTranscriptFound, 
            VideoUnavailable
        )
        
        # Create API instance
        api = YouTubeTranscriptApi()
        
        # Try to get transcript in English first
        try:
            transcript_list_obj = api.list(video_id)
            transcript = transcript_list_obj.find_transcript(['en'])
            transcript_data = transcript.fetch()
        except NoTranscriptFound:
            # Try to get any available transcript
            transcript_list_obj = api.list(video_id)
            transcript = transcript_list_obj.find_generated_transcript(['en'])
            transcript_data = transcript.fetch()
        
        # Combine all transcript segments into single text
        full_text = " ".join([entry['text'] for entry in transcript_data])
        
        # Calculate word count
        word_count = len(full_text.split())
        
        # Detect language from metadata
        language = transcript.language_code if hasattr(transcript, 'language_code') else 'en'
        
        return {
            "status": "success",
            "text": full_text,
            "language": language,
            "confidence": 1.0,  # YouTube captions are highly accurate
            "word_count": word_count,
            "source": "youtube_captions",
            "duration": transcript_data[-1]['start'] + transcript_data[-1]['duration'] if transcript_data else 0
        }
        
    except TranscriptsDisabled:
        return {
            "status": "failed",
            "text": None,
            "error": "Transcripts are disabled for this video"
        }
    
    except VideoUnavailable:
        return {
            "status": "failed",
            "text": None,
            "error": "Video is unavailable or private"
        }
    
    except NoTranscriptFound:
        return {
            "status": "failed",
            "text": None,
            "error": "No captions available in any language"
        }
    
    except ImportError:
        return {
            "status": "failed",
            "text": None,
            "error": "youtube-transcript-api not installed. Run: pip install youtube-transcript-api"
        }
    
    except Exception as e:
        return {
            "status": "failed",
            "text": None,
            "error": f"YouTube captions error: {str(e)}"
        }


def transcribe_with_vosk(video_id: str, log_callback=None) -> dict:
    """
    Vosk speech-to-text transcription (SLOW FALLBACK METHOD)
    
    Speed: 5-10 minutes per video
    Accuracy: Good
    Success Rate: ~70% (fails on long videos, no audio, corrupted files)
    
    Args:
        video_id: YouTube video ID
        log_callback: Optional callable(message: str) to send progress logs
    """
    try:
        from transcription_engine.vosk_worker import VoskTranscriber
        
        transcriber = VoskTranscriber(log_callback=log_callback)
        result = transcriber.transcribe_video(video_id)
        
        if result.get("text"):
            result["status"] = "success"
            result["source"] = "vosk"
            return result
        else:
            return {
                "status": "failed",
                "text": None,
                "error": result.get('error', 'Vosk returned empty transcript')
            }
            
    except ImportError as e:
        return {
            "status": "failed",
            "text": None,
            "error": f"Vosk import failed: {str(e)}"
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "text": None,
            "error": f"Vosk transcription error: {str(e)}"
        }



