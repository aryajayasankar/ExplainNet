import asyncio
import os
from sqlalchemy.orm import Session
from typing import Dict
from . import crud
from . import youtube_service
from . import news_service
from . import transcription_service
from . import huggingface_service
from . import gemini_service
from . import impact_score_service
from datetime import datetime


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
        
        # Process videos (all of them since we only fetched 10)
        print(f"⚙️  Step 4: Processing {len(videos)} videos...")
        for idx, video_data in enumerate(videos, 1):
            print(f"\n--- Processing video {idx}/{len(videos)} ---")
            await process_video(db, topic_id, video_data)
        
        print(f"\n✓ All {len(videos)} videos processed!\n")
        
        # Step 5: Search and analyze news articles (both recent and historical)
        print(f"📰 Step 5: Searching news articles...")
        print(f"   - Fetching recent news (NewsAPI)...")
        recent_articles = await news_service.search_articles(topic_name, max_results=2)
        print(f"   ✓ Found {len(recent_articles)} recent articles")
        
        print(f"   - Fetching historical news (Guardian)...")
        historical_articles = await news_service.search_guardian_articles(topic_name, max_results=2)
        print(f"   ✓ Found {len(historical_articles)} historical articles\n")
        
        # Tag articles by source type: recent (NewsAPI) vs historical (Guardian)
        for a in recent_articles:
            a["source_type"] = "recent"
        for a in historical_articles:
            a["source_type"] = "historical"

        all_articles = recent_articles + historical_articles
        
        print(f"📝 Summarizing {len(all_articles)} articles (Gemini gist only - NO sentiment analysis)...")
        
        # Gemini free tier: 10 requests per minute
        # Add 6-second delay between articles to avoid rate limits (10 articles/min = 6s each)
        import asyncio
        
        for idx, article_data in enumerate(all_articles, 1):
            article_title = article_data.get("title", "")
            article_description = article_data.get("description", "")
            article_content = article_data.get("content", "")
            
            if idx % 10 == 0 or idx == 1:
                print(f"   Processing article {idx}/{len(all_articles)}...")
            
            # Gemini summary/gist ONLY (no sentiment analysis)
            try:
                summary_result = await gemini_service.summarize_article(
                    title=article_title,
                    description=article_description,
                    content=article_content
                )
                # Store gist in gemini_justification field for now (reusing existing column)
                article_data["gemini_justification"] = summary_result.get("gist", "")
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    print(f"   ⚠️  Rate limit hit at article {idx}, waiting 60s...")
                    await asyncio.sleep(60)
                    # Retry once
                    try:
                        summary_result = await gemini_service.summarize_article(
                            title=article_title,
                            description=article_description,
                            content=article_content
                        )
                        article_data["gemini_justification"] = summary_result.get("gist", "")
                    except Exception as retry_e:
                        print(f"   ⚠️  Article {idx} summary failed after retry: {retry_e}")
                        article_data["gemini_justification"] = f"Summary unavailable (rate limit)"
                else:
                    print(f"   ⚠️  Article {idx} summary failed: {e}")
                    article_data["gemini_justification"] = f"Summary unavailable: {str(e)}"
            
            # Calculate relevance score (how closely article relates to topic)
            try:
                relevance = await gemini_service.calculate_news_relevance(topic_name, article_title)
                article_data["relevance_score"] = relevance
            except Exception as e:
                print(f"   ⚠️  Relevance calculation failed for article {idx}: {e}")
                article_data["relevance_score"] = 50  # Default middling score
            
            # Delay 6.5 seconds between articles (slightly over 6s for safety)
            # This ensures we stay under 10 requests/minute
            if idx < len(all_articles):  # Don't delay after last article
                await asyncio.sleep(6.5)
            
            # NO sentiment analysis for articles
            article_data["hf_sentiment"] = None
            article_data["hf_score"] = None
            article_data["hf_justification"] = None
            article_data["gemini_sentiment"] = None
            article_data["gemini_support"] = None
            article_data["gemini_score"] = None
            article_data["gemini_sarcasm_score"] = None
            article_data["overall_sentiment"] = None
            article_data["positive_score"] = None
            article_data["negative_score"] = None
            article_data["neutral_score"] = None
            
            # Skip entity extraction to reduce Gemini API calls (rate limit: 10/min on free tier)
            # This cuts API usage from 2 calls per article to 1 call per article
            article_data["entities_json"] = None
            article_data["entities"] = None
            
            # Save article to database
            crud.create_article(db, article_data, topic_id)
        
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
        
        print(f"\n{'#'*80}")
        print(f"✅ TOPIC ANALYSIS COMPLETE: {topic_name}")
        print(f"   Videos processed: {topic.total_videos}")
        print(f"   Articles found: {topic.total_articles}")
        print(f"   Status: {topic.analysis_status}")
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
    """Process a single video: transcribe, analyze sentiment, get comments"""
    
    try:
        video_id = video_data["video_id"]
        print(f"\n{'='*80}")
        print(f"🎬 Processing video: {video_data['title']}")
        print(f"   Video ID: {video_id}")
        print(f"{'='*80}")
        
        # Create video record
        print(f"✓ Creating video record in database...")
        # Remove is_valid field as it's not in the database model
        video_data_for_db = {k: v for k, v in video_data.items() if k != 'is_valid'}
        db_video = crud.create_video(db, video_data_for_db, topic_id)
        print(f"✓ Video record created with ID: {db_video.id}")
        
        # Step 4: Transcribe video
        print(f"\n📝 Transcribing video {video_id}...")
        try:
            transcript_result = transcription_service.transcribe_video(video_id)
            
            # Check transcription status
            status = transcript_result.get("status", "unknown")
            
            if status == "success" and transcript_result.get("text"):
                print(f"✓ Transcript received:")
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
                    print(f"📊 Analyzing {len(comments)} comments (VADER + Gemini)...")
                    
                    for idx, comment_data in enumerate(comments, 1):
                        comment_text = comment_data["text"]
                        
                        # Show progress every 10 comments
                        if idx % 10 == 0 or idx == 1:
                            print(f"   Processing comment {idx}/{len(comments)}...")
                        
                        # VADER sentiment analysis
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
                            print(f"      ⚠️ HF failed for comment {idx}: {str(hf_err)[:50]}")
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
                            # Small delay to avoid rate limiting
                            await asyncio.sleep(0.5)
                        except Exception as gemini_err:
                            print(f"      ⚠️ Gemini failed for comment {idx}: {str(gemini_err)[:50]}")
                            comment_data["gemini_sentiment"] = None
                            comment_data["gemini_support"] = None
                            comment_data["gemini_score"] = None
                        
                        # Save comment to database
                        try:
                            crud.create_comment(db, comment_data, db_video.id)
                        except Exception as save_err:
                            print(f"      ⚠️ Failed to save comment {idx}: {str(save_err)[:100]}")
                            db.rollback()  # Rollback this comment but continue with others
                    
                    print(f"✓ Analyzed and saved {len(comments)} comments to database")
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
