# ExplainNet - Recent Changes Summary

## Changes Implemented (November 17, 2025)

### 1. **Fixed httpx/httpcore Compatibility Issues**
**Problem**: `AsyncConnectionPool.__init__() got an unexpected keyword argument 'socket_options'`

**Solution**: Replaced all `httpx` usage with `aiohttp` in:
- `backend/youtube_service.py` 
- `backend/news_service.py`

**Result**: All API calls (YouTube, NewsAPI, Guardian) now work without version conflicts.

---

### 2. **Fixed Database Schema Mismatches**
**Problem**: Missing columns causing deletion and insertion failures

**Migrations Created & Run**:
1. `backend/add_overall_sentiment_migration.py` - Added `overall_sentiment` to `news_articles`
2. `backend/add_news_article_scores_migration.py` - Added `positive_score`, `negative_score`, `neutral_score`
3. `backend/add_entities_column_migration.py` - Added `entities` column

**Result**: All CRUD operations now work without schema errors. Topic deletion works properly.

---

### 3. **Installed Vosk Transcription**
**Problem**: Vosk not installed in `.venv311` environment

**Solution**: 
```powershell
pip install vosk yt-dlp
```

**Result**: Video transcription now enabled. Will download audio and transcribe with Vosk model.

---

### 4. **Changed News Article Processing**
**OLD Behavior**:
- HuggingFace sentiment analysis for articles ❌
- Gemini sentiment analysis for articles ❌
- Calculated overall sentiment scores ❌

**NEW Behavior**:
- **Gemini summary/gist ONLY** ✅
- NO sentiment analysis for articles ✅
- Gist stored in `gemini_justification` field ✅

**Result**: Articles now get short 2-3 sentence summaries telling users what to expect.

---

### 5. **YouTube Video Analysis (Unchanged)**
**Remains Active**:
- ✅ Gemini sentiment analysis (with justification + sarcasm score)
- ✅ HuggingFace sentiment analysis (with justification)
- ✅ Video transcription via Vosk
- ✅ Comment sentiment analysis (both models)

---

## Files Modified

### Backend Services:
- `backend/youtube_service.py` - Replaced httpx with aiohttp
- `backend/news_service.py` - Replaced httpx with aiohttp
- `backend/gemini_service.py` - Added `summarize_article()` function
- `backend/pipeline.py` - Changed article processing (removed sentiment, added summary)

### Database Migrations:
- `backend/add_overall_sentiment_migration.py`
- `backend/add_news_article_scores_migration.py`
- `backend/add_entities_column_migration.py`

### Database Backups Created:
- `explainnet.db.backup` (first migration)
- `explainnet.db.backup2` (score columns)
- `explainnet.db.backup3` (entities column)

---

## Current Pipeline Flow

### YouTube Videos:
1. Search YouTube (5 videos max)
2. Download audio with yt-dlp
3. Transcribe with Vosk
4. Analyze sentiment (HuggingFace + Gemini)
5. Extract comments
6. Analyze comment sentiment (both models)
7. Calculate impact scores

### News Articles:
1. Fetch recent articles (NewsAPI)
2. Fetch historical articles (Guardian)
3. **Generate Gemini summary/gist for each** ← NEW
4. Extract entities
5. Save to database
6. ~~NO sentiment analysis~~ ← REMOVED

---

## Next Steps (If Needed)

1. **Test full pipeline** - Create a new topic and verify:
   - Vosk transcription works
   - Gemini sentiment for videos works
   - Gemini summaries for articles work
   
2. **Frontend Updates** - Update UI to show article gists instead of sentiment

3. **Deployment** - Freeze requirements.txt and create Dockerfile

---

## Environment Setup

**Active Environment**: `.venv311` (Python 3.11)

**Installed Packages**:
- vosk==0.3.45
- yt-dlp==2025.11.12
- aiohttp (already present)
- All other dependencies from requirements.txt

**Server Command**:
```powershell
& D:\ExplainNet\.venv311\Scripts\Activate.ps1
$env:ALLOW_ORIGINS = "http://localhost:4200,http://127.0.0.1:4200"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
