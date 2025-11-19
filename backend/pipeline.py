import asyncio
import os
from sqlalchemy.orm import Session
from typing import Dict
import crud
import youtube_service
import news_service
import transcription_service
import huggingface_service
import gemini_service
import impact_score_service
import cache_service
from datetime import datetime

# Global queue for transcription logs
transcription_log_queue = None


async def analyze_topic_streaming(db: Session, topic_id: int, topic_name: str):
    """
    Streaming version of analyze_topic that yields progress messages for SSE
    
    Yields progress messages with format:
    {
        "status": "progress",
        "message": "User-friendly message",
        "type": "info" | "success" | "warning" | "error"
    }
    """
    
    global transcription_log_queue
    transcription_log_queue = asyncio.Queue()
    
    try:
        # Update status to processing
        crud.update_topic_status(db, topic_id, "processing")
        
        yield {"status": "progress", "message": "🔄 Initializing analysis pipeline...", "type": "info"}
        
        # Check cache first
        cached_result = cache_service.get_cached_topic_search(topic_name)
        if cached_result:
            yield {"status": "progress", "message": "💾 Found cached results!", "type": "success"}
            
            # Update topic with cached data
            topic = crud.get_topic(db, topic_id)
            topic.total_videos = cached_result.get('total_videos', 0)
            topic.total_articles = cached_result.get('total_articles', 0)
            topic.overall_impact_score = cached_result.get('overall_impact_score')
            topic.overall_sentiment = cached_result.get('overall_sentiment')
            topic.analysis_status = "completed"
            topic.last_analyzed_at = datetime.now()
            db.commit()
            
            yield {"status": "progress", "message": f"✅ Retrieved {cached_result.get('total_videos', 0)} videos and {cached_result.get('total_articles', 0)} articles from cache", "type": "success"}
            return
        
        # Verify API keys
        youtube_key = os.getenv("YOUTUBE_API_KEY")
        if not youtube_key:
            yield {"status": "error", "message": "❌ YouTube API key not configured", "type": "error"}
            raise ValueError("YOUTUBE_API_KEY not set")
        
        yield {"status": "progress", "message": "✅ API keys verified", "type": "success"}
        
        # Step 1: Search YouTube videos
        yield {"status": "progress", "message": f"🔍 Searching YouTube for \"{topic_name}\"...", "type": "info"}
        videos = await youtube_service.search_videos(topic_name, max_results=5)
        
        if not videos:
            yield {"status": "progress", "message": "❌ No videos found", "type": "error"}
            crud.update_topic_status(db, topic_id, "completed", "No videos found")
            return
        
        yield {"status": "progress", "message": f"✅ Found {len(videos)} videos", "type": "success"}
        
        # Step 2: Get video details and filter
        yield {"status": "progress", "message": "📋 Fetching video details...", "type": "info"}
        video_ids = [v["video_id"] for v in videos]
        video_details = await youtube_service.get_video_details(video_ids)
        
        # Filter for valid videos
        valid_video_details = [vd for vd in video_details if vd.get("is_valid", False)]
        valid_video_details = valid_video_details[:5]
        
        if not valid_video_details:
            yield {"status": "progress", "message": "❌ No valid videos found (filters: English, ≤35 mins)", "type": "error"}
            crud.update_topic_status(db, topic_id, "completed", "No valid videos found")
            return
        
        yield {"status": "progress", "message": f"✅ Filtered to {len(valid_video_details)} valid videos", "type": "success"}
        
        # Merge details
        video_details_map = {vd["video_id"]: vd for vd in valid_video_details}
        valid_videos = []
        for video in videos:
            vid = video["video_id"]
            if vid in video_details_map:
                video.update(video_details_map[vid])
                valid_videos.append(video)
        videos = valid_videos
        
        # Step 3: Get channel details
        yield {"status": "progress", "message": "👥 Fetching channel information...", "type": "info"}
        channel_ids = list(set([v.get("channel_id") for v in videos if v.get("channel_id")]))
        channel_details = await youtube_service.get_channel_details(channel_ids)
        channel_details_map = {cd["channel_id"]: cd for cd in channel_details}
        
        for video in videos:
            ch_id = video.get("channel_id")
            if ch_id and ch_id in channel_details_map:
                video["subscriber_count"] = channel_details_map[ch_id]["subscriber_count"]
            else:
                video["subscriber_count"] = 0
        
        yield {"status": "progress", "message": "✅ Channel data retrieved", "type": "success"}
        
        # Process videos IN PARALLEL with progress tracking
        yield {"status": "progress", "message": f"⚙️ Processing {len(videos)} videos...", "type": "info"}
        
        # Show first video title
        if videos:
            first_title = videos[0].get('title', '')[:60] + "..." if len(videos[0].get('title', '')) > 60 else videos[0].get('title', '')
            yield {"status": "progress", "message": f"📹 Video 1/{len(videos)}: {first_title}", "type": "info"}
        
        video_tasks = []
        for idx, video_data in enumerate(videos, 1):
            video_tasks.append(process_video_streaming(db, topic_id, video_data, idx, len(videos)))
        
        # Process videos and show progress
        yield {"status": "progress", "message": "🎙️ Transcribing audio...", "type": "info"}
        yield {"status": "progress", "message": "💭 Analyzing sentiment with AI...", "type": "info"}
        yield {"status": "progress", "message": "💬 Processing comments...", "type": "info"}
        
        # Gather results while monitoring transcription log queue
        results = []
        pending = {asyncio.create_task(task) for task in video_tasks}
        
        while pending:
            # Check queue for transcription logs (non-blocking)
            try:
                log_message = transcription_log_queue.get_nowait()
                print(f"[PIPELINE DEBUG] Got transcription log from queue: {log_message}")
                yield log_message  # Yield transcription log directly
            except asyncio.QueueEmpty:
                pass
            
            # Wait for any task to complete (with timeout to check queue frequently)
            done, pending = await asyncio.wait(pending, timeout=0.1, return_when=asyncio.FIRST_COMPLETED)
            results.extend([task.result() if not task.exception() else task.exception() for task in done])
        
        # Drain any remaining logs in queue
        while not transcription_log_queue.empty():
            try:
                log_message = transcription_log_queue.get_nowait()
                yield log_message
            except asyncio.QueueEmpty:
                break
        
        # Count successes
        successful = sum(1 for r in results if not isinstance(r, Exception))
        yield {"status": "progress", "message": f"✅ Processed {successful}/{len(videos)} videos successfully", "type": "success"}
        
        # Step 5: Search news articles
        yield {"status": "progress", "message": "📰 Searching news articles...", "type": "info"}
        
        recent_articles = []
        try:
            recent_articles = await news_service.search_articles(topic_name, max_results=2)
            if recent_articles:
                yield {"status": "progress", "message": f"✅ Found {len(recent_articles)} recent articles (NewsAPI)", "type": "success"}
        except Exception as e:
            yield {"status": "progress", "message": f"⚠️ NewsAPI unavailable, continuing...", "type": "warning"}
        
        historical_articles = []
        try:
            historical_articles = await news_service.search_guardian_articles(topic_name, max_results=2)
            if historical_articles:
                yield {"status": "progress", "message": f"✅ Found {len(historical_articles)} historical articles (Guardian)", "type": "success"}
        except Exception as e:
            yield {"status": "progress", "message": f"⚠️ Guardian API unavailable, continuing...", "type": "warning"}
        
        # Tag and combine articles
        for a in recent_articles:
            a["source_type"] = "recent"
        for a in historical_articles:
            a["source_type"] = "historical"
        all_articles = recent_articles + historical_articles
        
        if len(all_articles) == 0:
            yield {"status": "progress", "message": "⚠️ No news articles found", "type": "warning"}
        else:
            yield {"status": "progress", "message": f"📝 Summarizing {len(all_articles)} articles with AI...", "type": "info"}
            
            # Process articles with progress updates
            for idx, article in enumerate(all_articles, 1):
                try:
                    # Summarize article
                    summary_result = await gemini_service.summarize_article(
                        title=article.get("title", ""),
                        description=article.get("description", ""),
                        content=article.get("content", "")
                    )
                    article["gemini_justification"] = summary_result.get("gist", "")
                    
                    # Calculate relevance
                    try:
                        relevance = await gemini_service.calculate_news_relevance(topic_name, article.get("title", ""))
                        article["relevance_score"] = relevance
                    except Exception:
                        article["relevance_score"] = 50
                    
                    # Set sentiment fields to None (no sentiment analysis for articles)
                    article["hf_sentiment"] = None
                    article["hf_score"] = None
                    article["hf_justification"] = None
                    article["gemini_sentiment"] = None
                    article["gemini_support"] = None
                    article["gemini_score"] = None
                    article["gemini_sarcasm_score"] = None
                    article["overall_sentiment"] = None
                    article["positive_score"] = None
                    article["negative_score"] = None
                    article["neutral_score"] = None
                    article["entities_json"] = None
                    article["entities"] = None
                    
                    # Save to database
                    crud.create_article(db, article, topic_id)
                    
                    if idx % 2 == 0 or idx == len(all_articles):
                        yield {"status": "progress", "message": f"✅ Processed article {idx}/{len(all_articles)}", "type": "info"}
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(1)
                    
                except Exception as article_error:
                    yield {"status": "progress", "message": f"⚠️ Article {idx} failed: {str(article_error)[:50]}", "type": "warning"}
            
            yield {"status": "progress", "message": f"✅ All {len(all_articles)} articles summarized", "type": "success"}
        
        # Calculate statistics
        yield {"status": "progress", "message": "📊 Calculating final statistics...", "type": "info"}
        
        unique_sources = len(set([a.get("source", "") for a in all_articles if a.get("source")]))
        
        topic = crud.get_topic(db, topic_id)
        topic.total_videos = len(videos)
        topic.total_articles = len(all_articles)
        topic.unique_sources_count = unique_sources
        
        # Calculate average impact score
        all_videos = crud.get_videos_by_topic(db, topic_id)
        impact_scores = [v.impact_score for v in all_videos if v.impact_score is not None]
        if impact_scores:
            topic.overall_impact_score = sum(impact_scores) / len(impact_scores)
        
        # Determine overall sentiment
        sentiments = []
        for v in all_videos:
            video_sentiments = crud.get_sentiments_by_video(db, v.id)
            if video_sentiments:
                sentiments.append(video_sentiments[0].sentiment)
        
        filtered = [s for s in sentiments if s and str(s).upper() != 'UNKNOWN']
        if filtered:
            from collections import Counter
            sentiment_counts = Counter(filtered)
            topic.overall_sentiment = sentiment_counts.most_common(1)[0][0]
        else:
            topic.overall_sentiment = None
        
        topic.analysis_status = "completed"
        topic.last_analyzed_at = datetime.now()
        db.commit()
        
        # Cache results
        cache_data = {
            "total_videos": topic.total_videos,
            "total_articles": topic.total_articles,
            "overall_impact_score": topic.overall_impact_score,
            "overall_sentiment": topic.overall_sentiment,
            "analyzed_at": datetime.now().isoformat()
        }
        cache_service.cache_topic_search(topic_name, cache_data, ttl_seconds=900)
        
        yield {"status": "progress", "message": f"✅ Analysis complete! Impact score: {topic.overall_impact_score:.1f}/10" if topic.overall_impact_score else "✅ Analysis complete!", "type": "success"}
    
    except Exception as e:
        yield {"status": "error", "message": f"❌ Critical error: {str(e)[:100]}", "type": "error"}
        db.rollback()
        crud.update_topic_status(db, topic_id, "failed", str(e))


async def process_video_streaming(db: Session, topic_id: int, video_data: Dict, video_num: int, total_videos: int):
    """Streaming version of process_video - returns success/failure without yielding"""
    
    global transcription_log_queue
    
    def log_callback(message: str):
        """Callback to put transcription logs in queue"""
        print(f"[CALLBACK DEBUG] log_callback called with: {message}")
        if transcription_log_queue:
            # Put message in queue (will be consumed by analyze_topic_streaming)
            try:
                transcription_log_queue.put_nowait({"message": message})
                print(f"[CALLBACK DEBUG] Message added to queue successfully")
            except Exception as e:
                print(f"[CALLBACK DEBUG] Failed to add to queue: {e}")
                pass  # Queue might be full, skip
    
    try:
        video_id = video_data["video_id"]
        video_title = video_data['title'][:50] + "..." if len(video_data['title']) > 50 else video_data['title']
        
        # Check cache
        existing_video = db.query(crud.models.Video).filter(
            crud.models.Video.video_id == video_id
        ).first()
        
        if existing_video and existing_video.impact_score is not None:
            # Video already analyzed, reuse it
            return {"success": True, "message": f"Video {video_num} reused from cache"}
        
        # Create video record
        video_data_for_db = {k: v for k, v in video_data.items() if k != 'is_valid'}
        db_video = crud.create_video(db, video_data_for_db, topic_id)
        
        # Transcribe video with callback
        try:
            transcript_result = transcription_service.transcribe_video(video_id, log_callback=log_callback)
            status = transcript_result.get("status", "unknown")
            
            if status == "success" and transcript_result.get("text"):
                db_video.transcription_status = "success"
                db.commit()
            elif status == "timeout":
                db_video.transcription_status = "timeout"
                db_video.transcription_error = transcript_result.get("error", "Timeout")
                db.commit()
                transcript_result = {"text": None}
            else:
                db_video.transcription_status = "failed"
                db_video.transcription_error = transcript_result.get("error", "Unknown error")
                db.commit()
                transcript_result = {"text": None}
        except Exception as trans_error:
            db_video.transcription_status = "failed"
            db_video.transcription_error = str(trans_error)
            db.commit()
            transcript_result = {"text": None}
        
        hf_sentiment = None
        gemini_sentiment = None
        
        if transcript_result.get("text"):
            # Save transcript
            try:
                crud.create_transcript(db, transcript_result, db_video.id)
            except Exception:
                db.rollback()
            
            transcript_text = transcript_result["text"]
            
            # VADER sentiment
            try:
                hf_sentiment = await huggingface_service.analyze_sentiment(transcript_text)
                crud.create_sentiment(db, hf_sentiment, db_video.id)
            except Exception:
                pass
            
            # Gemini sentiment
            try:
                gemini_sentiment = await gemini_service.analyze_sentiment_advanced(
                    transcript_text,
                    video_data["title"]
                )
                crud.create_sentiment(db, gemini_sentiment, db_video.id)
            except Exception:
                pass
            
            # Extract entities
            try:
                entities = await gemini_service.extract_entities(
                    transcript_text,
                    context=video_data["title"]
                )
                import json
                db_video.entities_json = json.dumps(entities)
                db.commit()
            except Exception:
                pass
            
            # Get and analyze comments
            try:
                comments = await youtube_service.get_video_comments(video_id, max_results=20)
                
                if comments:
                    # Process comments in batches
                    async def analyze_comment(comment_data):
                        comment_text = comment_data["text"]
                        
                        try:
                            hf_result = await huggingface_service.analyze_sentiment(comment_text)
                            if isinstance(hf_result, dict) and hf_result.get("sentiment"):
                                comment_data["hf_sentiment"] = hf_result.get("sentiment")
                                comment_data["hf_score"] = hf_result.get("confidence", hf_result.get("score", 0.0))
                                comment_data["hf_justification"] = hf_result.get("justification")
                            else:
                                comment_data["hf_sentiment"] = None
                                comment_data["hf_score"] = None
                        except Exception:
                            comment_data["hf_sentiment"] = None
                            comment_data["hf_score"] = None
                        
                        try:
                            gemini_result = await gemini_service.analyze_comment_sentiment(comment_text)
                            if isinstance(gemini_result, dict) and gemini_result.get("sentiment"):
                                comment_data["gemini_sentiment"] = gemini_result.get("sentiment")
                                comment_data["gemini_support"] = gemini_result.get("support_stance")
                                comment_data["gemini_score"] = gemini_result.get("confidence", 0.0)
                                comment_data["gemini_justification"] = gemini_result.get("justification")
                                comment_data["gemini_sarcasm_score"] = gemini_result.get("sarcasm_score")
                            else:
                                comment_data["gemini_sentiment"] = None
                                comment_data["gemini_support"] = None
                                comment_data["gemini_score"] = None
                        except Exception:
                            comment_data["gemini_sentiment"] = None
                            comment_data["gemini_support"] = None
                            comment_data["gemini_score"] = None
                        
                        return comment_data
                    
                    # Process in batches
                    batch_size = 10
                    for i in range(0, len(comments), batch_size):
                        batch = comments[i:i+batch_size]
                        tasks = [analyze_comment(comment) for comment in batch]
                        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        for result in batch_results:
                            if isinstance(result, dict) and not isinstance(result, Exception):
                                try:
                                    crud.create_comment(db, result, db_video.id)
                                except Exception:
                                    db.rollback()
                        
                        if i + batch_size < len(comments):
                            await asyncio.sleep(1)
            except Exception:
                pass
        
        # Calculate impact scores
        try:
            sentiment_data = {
                "huggingface": hf_sentiment if hf_sentiment else None,
                "gemini": gemini_sentiment if gemini_sentiment else None
            } if (hf_sentiment or gemini_sentiment) else None

            scores = impact_score_service.calculate_impact_score(video_data, sentiment_data)

            if hf_sentiment and gemini_sentiment:
                overall_sentiment, models_agree = impact_score_service.determine_overall_sentiment(
                    hf_sentiment, gemini_sentiment
                )
                scores["overall_sentiment"] = overall_sentiment
                scores["models_agree"] = models_agree
            else:
                scores["overall_sentiment"] = None
                scores["models_agree"] = False

            crud.update_video_scores(db, db_video.id, scores)
        except Exception:
            db.rollback()
            raise
        
        return {"success": True, "message": f"Video {video_num} processed successfully"}
    
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Video {video_num} failed: {str(e)[:50]}"}


async def analyze_topic(db: Session, topic_id: int, topic_name: str):
    """
    Main pipeline to analyze a topic
    
    Steps:
    1. Search YouTube videos
    2. Get video details (views, likes, etc.)
    3. Get channel details (subscribers)
    4. Transcribe videos
    5. Analyze sentiment (VADER + Gemini)
    6. Get and analyze comments
    7. Calculate impact scores
    8. Search news articles
    9. Update topic status
    """
    
    try:
        # Update status to processing
        crud.update_topic_status(db, topic_id, "processing")
        
        print(f"\n{'#'*80}")
        print(f"🚀 STARTING TOPIC ANALYSIS: {topic_name}")
        print(f"   Topic ID: {topic_id}")
        print(f"{'#'*80}\n")
        
        # 💾 CHECK CACHE FIRST - Skip entire analysis if topic recently analyzed
        cached_result = cache_service.get_cached_topic_search(topic_name)
        if cached_result:
            print(f"💾💾💾 CACHE HIT! Topic '{topic_name}' already analyzed!")
            print(f"   ⚡ Returning cached results in <1 second!")
            print(f"   🎯 Cached videos: {cached_result.get('total_videos', 0)}")
            print(f"   🎯 Cached articles: {cached_result.get('total_articles', 0)}")
            
            # Update topic with cached data
            topic = crud.get_topic(db, topic_id)
            topic.total_videos = cached_result.get('total_videos', 0)
            topic.total_articles = cached_result.get('total_articles', 0)
            topic.overall_impact_score = cached_result.get('overall_impact_score')
            topic.overall_sentiment = cached_result.get('overall_sentiment')
            topic.analysis_status = "completed"
            topic.last_analyzed_at = datetime.now()
            db.commit()
            
            print(f"\n{'#'*80}")
            print(f"✅ TOPIC ANALYSIS COMPLETE (FROM CACHE): {topic_name}")
            print(f"   ⚡ Instant result!")
            print(f"{'#'*80}\n")
            return
        
        # No cache hit - proceed with full analysis
        print(f"🔍 NEW TOPIC - Starting full analysis...")
        
        # Verify API keys
        youtube_key = os.getenv("YOUTUBE_API_KEY")
        if not youtube_key:
            raise ValueError("❌ YOUTUBE_API_KEY not set in environment!")
        print(f"✓ YouTube API Key configured (length: {len(youtube_key)})")
        
        # Step 1: Search YouTube videos
        print(f"🔍 Step 1: Searching YouTube for: {topic_name}")
        videos = await youtube_service.search_videos(topic_name, max_results=5)  # Fetch 5 and analyze them
        print(f"✓ Found {len(videos)} videos\n")
        
        if not videos:
            print(f"❌ No videos found for topic: {topic_name}")
            crud.update_topic_status(db, topic_id, "completed", "No videos found")
            return
        
        # Step 2: Get video details (including duration and language)
        print(f"📋 Step 2: Getting video details and filtering...")
        video_ids = [v["video_id"] for v in videos]
        video_details = await youtube_service.get_video_details(video_ids)
        print(f"✓ Got details for {len(video_details)} videos")
        
        # Filter for valid videos (English, ≤35 minutes)
        valid_video_details = [vd for vd in video_details if vd.get("is_valid", False)]
        print(f"✓ Filtered to {len(valid_video_details)} valid videos (English, ≤35 mins)")
        
        # Keep only first 5 valid videos
        valid_video_details = valid_video_details[:5]
        print(f"✓ Keeping {len(valid_video_details)} videos for analysis\n")
        
        if not valid_video_details:
            print(f"❌ No valid videos found (all were either too long or non-English)")
            crud.update_topic_status(db, topic_id, "completed", "No valid videos found")
            return
        
        # Merge details with original video data
        video_details_map = {vd["video_id"]: vd for vd in valid_video_details}
        valid_videos = []
        for video in videos:
            vid = video["video_id"]
            if vid in video_details_map:
                video.update(video_details_map[vid])
                valid_videos.append(video)
        
        videos = valid_videos  # Replace with filtered list
        
        # Step 3: Get channel details
        channel_ids = list(set([v.get("channel_id") for v in videos if v.get("channel_id")]))
        channel_details = await youtube_service.get_channel_details(channel_ids)
        channel_details_map = {cd["channel_id"]: cd for cd in channel_details}
        
        for video in videos:
            ch_id = video.get("channel_id")
            if ch_id and ch_id in channel_details_map:
                video["subscriber_count"] = channel_details_map[ch_id]["subscriber_count"]
            else:
                video["subscriber_count"] = 0
        
        # Process videos IN PARALLEL (all of them at once)
        print(f"⚙️  Step 4: Processing {len(videos)} videos IN PARALLEL...")
        print(f"🚀 Starting parallel processing for {len(videos)} videos...")
        
        # Create tasks for all videos
        video_tasks = [
            process_video(db, topic_id, video_data)
            for video_data in videos
        ]
        
        # Process all videos simultaneously
        await asyncio.gather(*video_tasks, return_exceptions=True)
        
        print(f"\n✓ All {len(videos)} videos processed IN PARALLEL!\n")
        
        # Step 5: Search and analyze news articles (both recent and historical) with bypass
        print(f"📰 Step 5: Searching news articles...")
        print(f"   - Fetching recent news (NewsAPI)...")
        
        recent_articles = []
        try:
            recent_articles = await news_service.search_articles(topic_name, max_results=2)
            print(f"   ✓ Found {len(recent_articles)} recent articles")
        except Exception as e:
            print(f"   ⚠️  NewsAPI failed: {type(e).__name__}: {str(e)[:100]}")
            print(f"   → Continuing without recent articles...")
        
        print(f"   - Fetching historical news (Guardian)...")
        historical_articles = []
        try:
            historical_articles = await news_service.search_guardian_articles(topic_name, max_results=2)
            print(f"   ✓ Found {len(historical_articles)} historical articles\n")
        except Exception as e:
            print(f"   ⚠️  Guardian failed: {type(e).__name__}: {str(e)[:100]}")
            print(f"   → Continuing without historical articles...\n")
        
        # Tag articles by source type: recent (NewsAPI) vs historical (Guardian)
        for a in recent_articles:
            a["source_type"] = "recent"
        for a in historical_articles:
            a["source_type"] = "historical"

        all_articles = recent_articles + historical_articles
        
        if len(all_articles) == 0:
            print(f"⚠️  No news articles found (both APIs may be down or returned empty)")
            print(f"   → Continuing analysis without news data...\n")
        else:
            print(f"📝 Summarizing {len(all_articles)} articles (Gemini gist only - NO sentiment analysis)...")
            print(f"🚀 Processing articles in parallel batches of 5...")
        
        # Process articles in batches of 5 with exponential backoff
        async def process_article_with_retry(article_data, idx, total, topic_name):
            """Process a single article with retry logic"""
            article_title = article_data.get("title", "")
            article_description = article_data.get("description", "")
            article_content = article_data.get("content", "")
            
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    summary_result = await gemini_service.summarize_article(
                        title=article_title,
                        description=article_description,
                        content=article_content
                    )
                    article_data["gemini_justification"] = summary_result.get("gist", "")
                    
                    # Calculate relevance score
                    try:
                        relevance = await gemini_service.calculate_news_relevance(topic_name, article_title)
                        article_data["relevance_score"] = relevance
                    except Exception:
                        article_data["relevance_score"] = 50
                    
                    if idx % 5 == 0 or idx == 1:
                        print(f"   ✓ Processed article {idx}/{total}")
                    return
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "quota" in error_str.lower():
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) * 10  # Exponential backoff: 10s, 20s
                            print(f"   ⚠️  Rate limit hit at article {idx}, waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                        else:
                            article_data["gemini_justification"] = "Summary unavailable (rate limit)"
                            article_data["relevance_score"] = 50
                            print(f"   ⚠️  Article {idx} failed after retries")
                    else:
                        article_data["gemini_justification"] = f"Summary unavailable: {str(e)}"
                        article_data["relevance_score"] = 50
                        print(f"   ⚠️  Article {idx} error: {str(e)[:50]}")
                        break
        
        # Process in batches of 5 to respect rate limits (only if articles exist)
        if len(all_articles) > 0:
            batch_size = 5
            for i in range(0, len(all_articles), batch_size):
                batch = all_articles[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(all_articles) + batch_size - 1) // batch_size
                print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} articles)...")
                
                # Process batch in parallel
                tasks = [
                    process_article_with_retry(article, i+idx+1, len(all_articles), topic_name)
                    for idx, article in enumerate(batch)
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Small delay between batches (not between individual articles)
                if i + batch_size < len(all_articles):
                    await asyncio.sleep(2)  # Just 2 seconds between batches
            
            # Process each article's data after batch completion
            for article in all_articles:
                # NO sentiment analysis for articles
                article["hf_sentiment"] = None
                article["hf_score"] = None
                article["hf_justification"] = None
                article["gemini_sentiment"] = None
                article["gemini_support"] = None
                article["gemini_score"] = None
                article["gemini_sarcasm_score"] = None
                article["overall_sentiment"] = None
                article["positive_score"] = None
                article["negative_score"] = None
                article["neutral_score"] = None
                
                # Skip entity extraction to reduce Gemini API calls (rate limit: 10/min on free tier)
                # This cuts API usage from 2 calls per article to 1 call per article
                article["entities_json"] = None
                article["entities"] = None
                
                # Save article to database
                try:
                    crud.create_article(db, article, topic_id)
                except Exception as save_err:
                    print(f"   ⚠️  Failed to save article: {str(save_err)[:100]}")
            
            print(f"✓ All {len(all_articles)} articles summarized and saved\n")
        
        # Calculate source diversity
        unique_sources = len(set([a.get("source", "") for a in all_articles if a.get("source")]))
        print(f"📊 Source diversity: {unique_sources} unique news sources\n")
        
        # Update topic statistics
        print(f"📊 Updating topic statistics...")
        topic = crud.get_topic(db, topic_id)
        topic.total_videos = len(videos)  # All videos were processed
        topic.total_articles = len(all_articles)
        topic.unique_sources_count = unique_sources
        
        # Calculate average impact score from all videos
        all_videos = crud.get_videos_by_topic(db, topic_id)
        impact_scores = [v.impact_score for v in all_videos if v.impact_score is not None]
        if impact_scores:
            topic.overall_impact_score = sum(impact_scores) / len(impact_scores)
            print(f"✓ Average impact score: {topic.overall_impact_score:.2f}")
        
        # Determine overall sentiment from videos
        sentiments = []
        for v in all_videos:
            # Get the sentiment from the video's sentiments
            video_sentiments = crud.get_sentiments_by_video(db, v.id)
            if video_sentiments:
                # Take the first sentiment (VADER usually)
                sentiments.append(video_sentiments[0].sentiment)
        
        # Filter out UNKNOWN or None sentiments
        filtered = [s for s in sentiments if s and str(s).upper() != 'UNKNOWN']
        if filtered:
            from collections import Counter
            sentiment_counts = Counter(filtered)
            topic.overall_sentiment = sentiment_counts.most_common(1)[0][0]
            print(f"✓ Overall sentiment: {topic.overall_sentiment}")
        else:
            topic.overall_sentiment = None
            print("✓ Overall sentiment: None (no reliable model labels)")
        
        topic.analysis_status = "completed"
        topic.last_analyzed_at = datetime.now()
        db.commit()
        
        # 💾 CACHE THE RESULTS for future searches (15 min TTL)
        cache_data = {
            "total_videos": topic.total_videos,
            "total_articles": topic.total_articles,
            "overall_impact_score": topic.overall_impact_score,
            "overall_sentiment": topic.overall_sentiment,
            "analyzed_at": datetime.now().isoformat()
        }
        cache_service.cache_topic_search(topic_name, cache_data, ttl_seconds=900)  # 15 min
        
        print(f"\n{'#'*80}")
        print(f"✅ TOPIC ANALYSIS COMPLETE: {topic_name}")
        print(f"   Videos processed: {topic.total_videos}")
        print(f"   Articles found: {topic.total_articles}")
        print(f"   Status: {topic.analysis_status}")
        print(f"   💾 Results cached for 15 minutes")
        print(f"{'#'*80}\n")
    
    except Exception as e:
        print(f"\n{'#'*80}")
        print(f"❌ CRITICAL ERROR analyzing topic: {topic_name}")
        print(f"   Error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Full traceback:\n{traceback.format_exc()}")
        print(f"\n{'#'*80}\n")
        # Rollback session before updating status
        db.rollback()
        crud.update_topic_status(db, topic_id, "failed", str(e))


async def process_video(db: Session, topic_id: int, video_data: Dict):
    """Process a single video: transcribe, analyze sentiment, get comments
    
    OPTIMIZED: Checks cache first - skips processing if video already analyzed
    """
    
    try:
        video_id = video_data["video_id"]
        print(f"\n{'='*80}")
        print(f"🎬 Processing video: {video_data['title']}")
        print(f"   Video ID: {video_id}")
        print(f"{'='*80}")
        
        # 🚀 CACHE CHECK: See if this video was already analyzed
        existing_video = db.query(crud.models.Video).filter(
            crud.models.Video.video_id == video_id
        ).first()
        
        if existing_video and existing_video.impact_score is not None:
            # Video already fully analyzed! Reuse it for this topic
            print(f"💾 CACHE HIT! Video already analyzed (ID: {existing_video.id})")
            print(f"   ✓ Sentiment: {existing_video.overall_sentiment}")
            print(f"   ✓ Impact Score: {existing_video.impact_score}")
            print(f"   ✓ Transcript: {'Yes' if existing_video.transcript else 'No'}")
            print(f"   ✓ Comments: {len(existing_video.comments)} cached")
            print(f"   🚀 SKIPPING full analysis, linking to topic...")
            
            # Just link this video to the new topic (if not already linked)
            if existing_video.topic_id != topic_id:
                # Create a reference/duplicate for this topic
                # OR update the topic_id (depending on your business logic)
                # For now, we'll just return and reuse the same video
                pass
            
            print(f"✅ Video reused from cache in ~0.1 seconds!\n")
            return
        
        # No cache hit - proceed with full analysis
        print(f"🔍 NEW VIDEO - Starting full analysis...")
        
        # Create video record
        print(f"✓ Creating video record in database...")
        # Remove is_valid field as it's not in the database model
        video_data_for_db = {k: v for k, v in video_data.items() if k != 'is_valid'}
        db_video = crud.create_video(db, video_data_for_db, topic_id)
        print(f"✓ Video record created with ID: {db_video.id}")
        
        # Step 4: Transcribe video (HYBRID: YouTube Captions → Vosk Fallback)
        print(f"\n📝 Transcribing video {video_id}...")
        try:
            transcript_result = transcription_service.transcribe_video(video_id)
            
            # Check transcription status
            status = transcript_result.get("status", "unknown")
            source = transcript_result.get("source", "unknown")
            
            if status == "success" and transcript_result.get("text"):
                # Show which method was used
                if source == "youtube_captions":
                    print(f"✓ Transcript received via YouTube Captions ⚡ (FAST)")
                elif source == "vosk":
                    print(f"✓ Transcript received via Vosk 🐌 (SLOW)")
                else:
                    print(f"✓ Transcript received via {source}")
                
                print(f"   - Text length: {len(transcript_result.get('text', ''))} characters")
                print(f"   - Language: {transcript_result.get('language', 'unknown')}")
                print(f"   - Word count: {transcript_result.get('word_count', 0)}")
                print(f"   - Duration: {transcript_result.get('duration', 0)}s")
                
                # Update video transcription status
                db_video.transcription_status = "success"
                db.commit()
                
            elif status == "timeout":
                print(f"⏱️  TIMEOUT: Transcription exceeded 5 minutes")
                db_video.transcription_status = "timeout"
                db_video.transcription_error = transcript_result.get("error", "Timeout")
                db.commit()
                transcript_result = {"text": None}
                
            else:
                error_msg = transcript_result.get("error", "Unknown error")
                print(f"⚠️  FAILED: {error_msg}")
                db_video.transcription_status = "failed"
                db_video.transcription_error = error_msg
                db.commit()
                transcript_result = {"text": None}
                
        except Exception as trans_error:
            print(f"✗ TRANSCRIPTION EXCEPTION: {str(trans_error)}")
            db_video.transcription_status = "failed"
            db_video.transcription_error = str(trans_error)
            db.commit()
            transcript_result = {"text": None}
        
        hf_sentiment = None
        gemini_sentiment = None
        
        if transcript_result["text"]:
            print(f"\n✓ Transcript available, creating database record...")
            try:
                crud.create_transcript(db, transcript_result, db_video.id)
                print(f"✓ Transcript saved to database")
            except Exception as transcript_save_error:
                print(f"✗ Error saving transcript: {transcript_save_error}")
                db.rollback()
                # Continue processing even if transcript save fails
            
            # Step 5: Analyze sentiment (both models)
            transcript_text = transcript_result["text"]
            
            # VADER sentiment (free, local)
            print(f"\n🤖 Analyzing sentiment with VADER...")
            try:
                hf_sentiment = await huggingface_service.analyze_sentiment(transcript_text)
                print(f"✓ VADER sentiment: {hf_sentiment.get('sentiment', 'unknown')}")
                print(f"   - Score: {hf_sentiment.get('confidence', 0)}")
                crud.create_sentiment(db, hf_sentiment, db_video.id)
                print(f"✓ VADER sentiment saved to database")
            except Exception as hf_error:
                print(f"✗ VADER SENTIMENT FAILED: {str(hf_error)}")
            
            # Gemini sentiment
            print(f"\n🧠 Analyzing sentiment with Gemini...")
            try:
                gemini_sentiment = await gemini_service.analyze_sentiment_advanced(
                    transcript_text,
                    video_data["title"]
                )
                print(f"✓ Gemini sentiment: {gemini_sentiment.get('sentiment', 'unknown')}")
                print(f"   - Emotional tone: {gemini_sentiment.get('emotional_tone', 'unknown')}")
                print(f"   - Bias level: {gemini_sentiment.get('bias_level', 'unknown')}")
                crud.create_sentiment(db, gemini_sentiment, db_video.id)
                print(f"✓ Gemini sentiment saved to database")
            except Exception as gemini_error:
                print(f"✗ GEMINI SENTIMENT FAILED: {str(gemini_error)}")
            
            # Step 5.5: Extract entities from transcript
            print(f"\n🔍 Extracting entities with Gemini...")
            try:
                entities = await gemini_service.extract_entities(
                    transcript_text,
                    context=video_data["title"]
                )
                
                # Count entities
                entity_counts = {k: len(v) for k, v in entities.items()}
                print(f"✓ Entities extracted:")
                print(f"   - Persons: {entity_counts.get('persons', 0)}")
                print(f"   - Organizations: {entity_counts.get('organizations', 0)}")
                print(f"   - Locations: {entity_counts.get('locations', 0)}")
                
                # Store as JSON in video record
                import json
                db_video.entities_json = json.dumps(entities)
                db.commit()
                print(f"✓ Entities saved to database")
                
            except Exception as entity_error:
                print(f"✗ ENTITY EXTRACTION FAILED: {str(entity_error)}")
            
            # Step 6: Get and analyze comments (20 comments, analyze with HF + Gemini)
            print(f"💬 Fetching comments...")
            try:
                comments = await youtube_service.get_video_comments(video_id, max_results=20)
                print(f"✓ Found {len(comments)} comments")
                
                if comments:
                    print(f"📊 Analyzing {len(comments)} comments (VADER + Gemini) IN PARALLEL...")
                    
                    # Process comments in batches of 10
                    async def analyze_comment(comment_data, idx):
                        """Analyze a single comment with both models"""
                        comment_text = comment_data["text"]
                        
                        # VADER sentiment analysis (fast, local)
                        try:
                            hf_result = await huggingface_service.analyze_sentiment(comment_text)
                            if isinstance(hf_result, dict) and hf_result.get("sentiment"):
                                comment_data["hf_sentiment"] = hf_result.get("sentiment")
                                comment_data["hf_score"] = hf_result.get("confidence", hf_result.get("score", 0.0))
                                comment_data["hf_justification"] = hf_result.get("justification")
                            else:
                                comment_data["hf_sentiment"] = None
                                comment_data["hf_score"] = None
                        except Exception as hf_err:
                            comment_data["hf_sentiment"] = None
                            comment_data["hf_score"] = None
                        
                        # Gemini sentiment analysis
                        try:
                            gemini_result = await gemini_service.analyze_comment_sentiment(comment_text)
                            if isinstance(gemini_result, dict) and gemini_result.get("sentiment"):
                                comment_data["gemini_sentiment"] = gemini_result.get("sentiment")
                                comment_data["gemini_support"] = gemini_result.get("support_stance")
                                comment_data["gemini_score"] = gemini_result.get("confidence", 0.0)
                                comment_data["gemini_justification"] = gemini_result.get("justification")
                                comment_data["gemini_sarcasm_score"] = gemini_result.get("sarcasm_score")
                            else:
                                comment_data["gemini_sentiment"] = None
                                comment_data["gemini_support"] = None
                                comment_data["gemini_score"] = None
                        except Exception as gemini_err:
                            comment_data["gemini_sentiment"] = None
                            comment_data["gemini_support"] = None
                            comment_data["gemini_score"] = None
                        
                        return comment_data
                    
                    # Process in batches of 10 comments
                    batch_size = 10
                    analyzed_comments = []
                    
                    for i in range(0, len(comments), batch_size):
                        batch = comments[i:i+batch_size]
                        batch_num = (i // batch_size) + 1
                        total_batches = (len(comments) + batch_size - 1) // batch_size
                        print(f"   Processing comment batch {batch_num}/{total_batches} ({len(batch)} comments)...")
                        
                        # Analyze batch in parallel
                        tasks = [
                            analyze_comment(comment, i+idx+1)
                            for idx, comment in enumerate(batch)
                        ]
                        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # Filter out exceptions and save to database
                        for result in batch_results:
                            if isinstance(result, dict) and not isinstance(result, Exception):
                                try:
                                    crud.create_comment(db, result, db_video.id)
                                    analyzed_comments.append(result)
                                except Exception as save_err:
                                    print(f"      ⚠️ Failed to save comment: {str(save_err)[:100]}")
                                    db.rollback()
                        
                        # Small delay between batches to avoid rate limits
                        if i + batch_size < len(comments):
                            await asyncio.sleep(1)
                    
                    print(f"✓ Analyzed and saved {len(analyzed_comments)} comments to database")
                else:
                    print(f"   No comments found for this video")
                    
            except Exception as comment_error:
                print(f"✗ COMMENT ANALYSIS FAILED: {str(comment_error)}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()[:200]}")
        else:
            print(f"\n⚠️  No transcript available, skipping sentiment analysis and comments")
        
        # Step 7: Calculate impact scores (even without transcript)
        print(f"\n📊 Calculating impact score...")
        print(f"   Video data: views={video_data.get('view_count', 0)}, likes={video_data.get('like_count', 0)}")
        try:
            # Build sentiment_data if at least one model produced results
            sentiment_data = {
                "huggingface": hf_sentiment if hf_sentiment else None,
                "gemini": gemini_sentiment if gemini_sentiment else None
            } if (hf_sentiment or gemini_sentiment) else None

            scores = impact_score_service.calculate_impact_score(video_data, sentiment_data)
            print(f"✓ Impact score calculated:")
            print(f"   - Overall: {scores.get('impact_score', 0)}")
            print(f"   - Reach: {scores.get('reach_score', 0)}")
            print(f"   - Engagement: {scores.get('engagement_score', 0)}")
            print(f"   - Sentiment: {scores.get('sentiment_score', 0)}")

            # Determine overall sentiment and agreement
            if hf_sentiment and gemini_sentiment:
                overall_sentiment, models_agree = impact_score_service.determine_overall_sentiment(
                    hf_sentiment, gemini_sentiment
                )
                scores["overall_sentiment"] = overall_sentiment
                scores["models_agree"] = models_agree
                print(f"✓ Overall sentiment: {overall_sentiment} (models agree: {models_agree})")
            else:
                scores["overall_sentiment"] = None
                scores["models_agree"] = False
                print(f"⚠️  No overall sentiment (missing sentiment data)")

            crud.update_video_scores(db, db_video.id, scores)
            print(f"✓ Scores saved to database")
            print(f"\n{'='*80}")
            print(f"✅ Video processing complete: {video_data['title'][:50]}...")
            print(f"{'='*80}\n")
        except Exception as score_error:
            print(f"✗ IMPACT SCORE CALCULATION FAILED: {str(score_error)}")
            raise
    
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"❌ ERROR processing video {video_data.get('video_id', 'unknown')}")
        print(f"   Error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        print(f"\n{'='*80}\n")
        # Rollback the session to clear error state
        db.rollback()
