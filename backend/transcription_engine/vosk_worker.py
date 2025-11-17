"""
Vosk-based Transcription Worker
Downloads audio and processes with Vosk
"""
import os
import json
import subprocess
import time
import tempfile
import yt_dlp
import signal
from contextlib import contextmanager
from vosk import Model, KaldiRecognizer
from typing import Dict, Optional
from pathlib import Path

# Model path (relative to this file)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "vosk-model-small-en-us-0.15")

# Timeout settings
TRANSCRIPTION_TIMEOUT = 300  # 5 minutes in seconds


class TimeoutException(Exception):
    """Raised when transcription times out"""
    pass


@contextmanager
def timeout(seconds):
    """Context manager for timeout (Windows compatible using threading)"""
    import threading
    
    def timeout_handler():
        raise TimeoutException(f"Operation timed out after {seconds} seconds")
    
    timer = threading.Timer(seconds, timeout_handler)
    timer.start()
    try:
        yield
    finally:
        timer.cancel()


class VoskTranscriber:
    """Vosk transcription engine for YouTube videos"""
    
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load Vosk model (lazy loading)"""
        if not os.path.exists(MODEL_PATH):
            print(f"⚠️  Vosk model not found at: {MODEL_PATH}")
            print(f"   Please download from: https://alphacephei.com/vosk/models")
            print(f"   Recommended: vosk-model-small-en-us-0.15")
            return False
        
        if not self.model:
            print(f"📦 Loading Vosk model from {MODEL_PATH}...")
            self.model = Model(MODEL_PATH)
            print(f"✓ Vosk model loaded successfully")
        
        return True
    
    def get_audio_stream_url(self, video_url: str) -> Optional[str]:
        """Get direct audio stream URL using yt-dlp"""
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
            }
            
            stream_url = None
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                # Try to find audio-only stream first
                for f in info['formats']:
                    if (f.get('vcodec') == 'none' and 
                        f.get('acodec') != 'none' and 
                        f.get('url')):
                        stream_url = f['url']
                        break
                
                # Fallback to best stream with audio
                if not stream_url:
                    for f in info['formats']:
                        if f.get('acodec') != 'none' and f.get('url'):
                            stream_url = f['url']
                            break
            
            return stream_url
        
        except Exception as e:
            print(f"   yt-dlp error: {str(e)}")
            return None
    
    def transcribe_video(self, video_id: str) -> Dict:
        """
        Transcribe a YouTube video using Vosk with 5-minute timeout
        Downloads audio using yt-dlp, converts to WAV, then transcribes
        
        Returns:
            Dict with text, language, confidence, word_count, status
        """
        if not self.load_model():
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "word_count": 0,
                "source": "vosk",
                "status": "failed",
                "error": "Model not loaded"
            }
        
        try:
            # Wrap entire transcription in timeout
            with timeout(TRANSCRIPTION_TIMEOUT):
                return self._transcribe_with_timeout(video_id)
                
        except TimeoutException as e:
            print(f"   ⏱️  Transcription TIMEOUT after {TRANSCRIPTION_TIMEOUT} seconds")
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "word_count": 0,
                "source": "vosk",
                "status": "timeout",
                "error": f"Transcription exceeded {TRANSCRIPTION_TIMEOUT} seconds timeout"
            }
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "word_count": 0,
                "source": "vosk",
                "status": "failed",
                "error": str(e)
            }
    
    def _transcribe_with_timeout(self, video_id: str) -> Dict:
        """Internal transcription method (called within timeout context)"""
        audio_file = None
        wav_file = None
        start_time = time.time()
        
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Create temp files with unique names
            audio_file = tempfile.NamedTemporaryFile(suffix=f'_{video_id}.m4a', delete=False)
            wav_file = tempfile.NamedTemporaryFile(suffix=f'_{video_id}.wav', delete=False)
            audio_file.close()
            wav_file.close()
            
            # Delete if already exists
            if os.path.exists(audio_file.name):
                os.unlink(audio_file.name)
            if os.path.exists(wav_file.name):
                os.unlink(wav_file.name)
            
            # Download audio using yt-dlp
            print(f"   Downloading audio with yt-dlp...")
            ydl_opts = {
                'format': 'worstaudio/worst',  # Use worst quality to avoid 403 on premium formats
                'outtmpl': audio_file.name,
                'quiet': False,
                'no_warnings': False,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'extractor_retries': 3,
                'fragment_retries': 3,
                'skip_unavailable_fragments': True,  # Skip unavailable fragments instead of failing
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                }
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Check if file was downloaded
            if not os.path.exists(audio_file.name) or os.path.getsize(audio_file.name) == 0:
                raise Exception("Download failed - file is empty")
            
            print(f"   Downloaded {os.path.getsize(audio_file.name)} bytes")
            
            # Convert to WAV using ffmpeg
            print(f"   Converting to WAV...")
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', audio_file.name,
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',       # Mono
                '-f', 'wav',      # WAV format
                '-y',             # Overwrite
                wav_file.name
            ]
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg conversion failed: {result.stderr[:200]}")
            
            if not os.path.exists(wav_file.name) or os.path.getsize(wav_file.name) == 0:
                raise Exception("WAV conversion failed - file is empty")
            
            print(f"   WAV file created: {os.path.getsize(wav_file.name)} bytes")
            
            # Transcribe with Vosk
            print(f"   Transcribing...")
            recognizer = KaldiRecognizer(self.model, 16000)
            recognizer.SetWords(True)
            
            full_text_segments = []
            
            with open(wav_file.name, 'rb') as wf:
                # Skip WAV header (44 bytes)
                wf.seek(44)
                
                while True:
                    data = wf.read(4096)
                    if not data:
                        break
                    
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get('text', '').strip()
                        if text:
                            full_text_segments.append(text)
                
                # Get final result
                final_result = json.loads(recognizer.FinalResult())
                final_text = final_result.get('text', '').strip()
                if final_text:
                    full_text_segments.append(final_text)
            
            # Join all segments
            full_text = " ".join(full_text_segments)
            
            if not full_text.strip():
                raise Exception("Transcription resulted in empty text")
            
            duration = round(time.time() - start_time, 2)
            word_count = len(full_text.split())
            
            print(f"   ✓ Transcription complete: {word_count} words in {duration}s")
            
            return {
                "text": full_text,
                "language": "en",
                "confidence": 0.85,
                "word_count": word_count,
                "source": "vosk",
                "status": "success",
                "duration": duration
            }
        
        except Exception as e:
            print(f"   Vosk transcription error: {str(e)}")
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "word_count": 0,
                "source": "vosk",
                "status": "failed",
                "error": str(e)
            }
        
        finally:
            # Clean up temp files
            try:
                if audio_file and os.path.exists(audio_file.name):
                    os.unlink(audio_file.name)
                if wav_file and os.path.exists(wav_file.name):
                    os.unlink(wav_file.name)
            except:
                pass

        if not self.load_model():
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "word_count": 0,
                "source": "vosk",
                "error": "Model not loaded"
            }
        
        audio_file = None
        start_time = time.time()
        
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
                audio_file = tmp.name
            
            print(f"   Downloading audio to temporary file...")
            
            # Download audio using yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_file,
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            print(f"   Audio downloaded, converting and transcribing...")
            
            # Set up Vosk recognizer
            recognizer = KaldiRecognizer(self.model, 16000)
            recognizer.SetWords(True)
            
            # Convert audio with ffmpeg and pipe to Vosk
            ffmpeg_command = [
                "ffmpeg",
                "-loglevel", "warning",
                "-i", audio_file,
                "-vn",  # No video
                "-f", "s16le",
                "-ar", "16000",
                "-ac", "1",
                "-t", "300",  # Limit to 5 minutes max
                "pipe:1"  # Output to stdout
            ]
            
            # Start ffmpeg subprocess
            process = subprocess.Popen(
                ffmpeg_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            
            # Process audio chunks
            full_text_segments = []
            bytes_read = 0
            chunks_processed = 0
            
            print(f"   Processing audio stream...")
            
            while True:
                data = process.stdout.read(4096)
                if not data:
                    break
                
                bytes_read += len(data)
                chunks_processed += 1
                
                # Progress indicator every 100 chunks (~400KB)
                if chunks_processed % 100 == 0:
                    mb_read = bytes_read / (1024 * 1024)
                    print(f"   ... {mb_read:.1f}MB processed, {len(full_text_segments)} segments so far")
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        full_text_segments.append(text)
                        print(f"   📝 Segment: {text[:50]}...")  # Show first 50 chars
            
            # Get final result
            print(f"   Getting final result... ({chunks_processed} chunks, {bytes_read} bytes)")
            final_result = json.loads(recognizer.FinalResult())
            final_text = final_result.get('text', '').strip()
            if final_text:
                full_text_segments.append(final_text)
                print(f"   📝 Final: {final_text[:50]}...")
            
            # Check for ffmpeg errors
            stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
            if stderr_output:
                print(f"   ⚠️  FFmpeg warnings/errors:\n{stderr_output[:500]}")
            
            # Join all segments
            full_text = " ".join(full_text_segments)
            
            print(f"   Total segments: {len(full_text_segments)}, Total text length: {len(full_text)}")
            
            if not full_text.strip():
                error_msg = f"Transcription resulted in empty text. Bytes read: {bytes_read}, Chunks: {chunks_processed}"
                if stderr_output:
                    error_msg += f"\nFFmpeg output: {stderr_output[:200]}"
                raise Exception(error_msg)
            
            duration = round(time.time() - start_time, 2)
            word_count = len(full_text.split())
            
            print(f"   ✓ Transcription complete: {word_count} words in {duration}s")
            
            return {
                "text": full_text,
                "language": "en",
                "confidence": 0.85,  # Vosk confidence
                "word_count": word_count,
                "source": "vosk",
                "duration": duration
            }
        
        except Exception as e:
            print(f"   Vosk transcription error: {str(e)}")
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "word_count": 0,
                "source": "vosk",
                "error": str(e)
            }
        
        finally:
            # Clean up process
            if 'process' in locals() and process:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                except Exception:
                    pass
            
            # Clean up temporary audio file
            if audio_file and os.path.exists(audio_file):
                try:
                    os.unlink(audio_file)
                except Exception:
                    pass


# Global instance
_transcriber = None

def get_transcriber():
    """Get or create global transcriber instance"""
    global _transcriber
    if _transcriber is None:
        _transcriber = VoskTranscriber()
    return _transcriber
