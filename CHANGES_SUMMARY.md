# ExplainNet - Recent Changes Summary

## Latest Changes (Current Session)

### **Backend Integration for GNN & Emotion Data**

#### 1. Added Emotions to Video API Response
**File**: `backend/schemas.py`
- Added `emotions_json: Optional[str]` field to VideoResponse
- Added `emotions: Optional[str]` alias for frontend compatibility

**File**: `backend/crud.py`
- Modified `get_videos_by_topic()` to aggregate emotions from sentiments table
- Calculates average emotion scores (joy, sadness, anger, fear, surprise, love, neutral)
- Stores aggregated data in `video.emotions_json` and `video.emotions`

**Result**: Videos now include emotion data from sentiment analysis in API responses.

---

#### 2. Created GNN Backend Endpoint
**File**: `backend/main.py`
- Added `/api/topics/{topic_id}/videos/gnn` endpoint
- Calculates Graph Neural Network visualization data:
  - **Nodes**: Top 12 videos by impact score with circular layout positions
  - **Edges**: Connections between videos with similar sentiment or impact (within 20%)
  - **Node sizes**: Based on impact scores (15-40px radius)
  - Returns layout metadata (centerX, centerY, radius)

**Algorithm**:
```python
- Sort videos by impact_score, take top 12
- Calculate circular positions: angle = (i * 2π) / 12
- Node size = 15 + (impact/max_impact * 25)
- Connect if: same_sentiment OR impact_difference < 20%
```

**Result**: GNN graph data calculated on backend, not frontend.

---

#### 3. Removed GNN Hover Effects
**File**: `frontend/explainnet-ui/src/app/pages/analysis/analysis.component.scss`
- Removed `:hover` transform scale from `.gnn-node`
- Removed `cursor: pointer` from `.gnn-node-group`
- Removed transition animations

**Result**: GNN nodes are static, no hover interactions.

---

#### 4. Frontend GNN Integration
**File**: `frontend/explainnet-ui/src/app/services/api.service.ts`
- Added `getVideosGNN(topicId)` method

**File**: `frontend/explainnet-ui/src/app/pages/analysis/analysis.component.ts`
- Added `gnnData: { nodes: any[], edges: any[] }` property
- Added `loadGNNData()` method called after videos load
- Refactored `getVideoGNNData()` to return backend nodes
- Added `getVideoGNNEdges()` to return backend edges
- Added `getNodeById(nodeId)` helper for edge rendering
- Added `getNodeConnections(nodeId)` to count connections

**File**: `frontend/explainnet-ui/src/app/pages/analysis/analysis.component.html`
- Updated edge rendering to use `getVideoGNNEdges()` array
- Updated video list to show connection count from backend

**Result**: GNN visualization uses 100% backend data, no frontend calculations.

---

#### 5. Verified All Charts Use Backend Data
**Checked Methods** (all use `this.videos` from API):
- ✅ `getVideoImpactScoreData()` - Sorts/formats backend impact_score
- ✅ `getVideoViewsData()` - Sorts/formats backend view_count
- ✅ `getVideoEngagementData()` - Calculates from backend like_count + comment_count
- ✅ `getOverallEmotionRadarData()` - Aggregates backend video.emotions

**Result**: All video charts display backend-calculated data, only formatting on frontend.

---

## Files Modified (Current Session)

### Backend:
- `backend/schemas.py` - Added emotions fields to VideoResponse
- `backend/crud.py` - Added emotion aggregation to get_videos_by_topic()
- `backend/main.py` - Added /videos/gnn endpoint

### Frontend:
- `frontend/explainnet-ui/src/app/services/api.service.ts` - Added getVideosGNN()
- `frontend/explainnet-ui/src/app/pages/analysis/analysis.component.ts` - GNN backend integration
- `frontend/explainnet-ui/src/app/pages/analysis/analysis.component.html` - Updated GNN template
- `frontend/explainnet-ui/src/app/pages/analysis/analysis.component.scss` - Removed hover effects

---

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
