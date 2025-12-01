"""
Data Collection Script for Research Dataset
============================================
Collects 125 YouTube videos + news articles using existing ExplainNet pipeline.

Usage:
    python 02_data_collection.py
"""

import sys
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.pipeline import analyze_topic_streaming
from backend.database import get_db
from backend.crud import get_videos_by_topic, get_articles_by_topic
from scripts.topic_selection import RESEARCH_TOPICS, get_all_topics

OUTPUT_DIR = Path(__file__).parent.parent / 'data'
OUTPUT_FILE = OUTPUT_DIR / 'research_dataset_raw.json'

async def collect_videos_for_topic(topic_name, domain):
    """
    Collect videos for a single topic using existing pipeline.
    
    Args:
        topic_name: The search query topic
        domain: Category (health, politics, etc.)
    
    Returns:
        List of video dictionaries
    """
    print(f"\n{'='*80}")
    print(f"COLLECTING: {topic_name} ({domain})")
    print(f"{'='*80}")
    
    try:
        # Run ExplainNet pipeline
        topic_id = None
        async for message in analyze_topic_streaming(topic_name):
            if message.get('type') == 'topic_created':
                topic_id = message.get('topic_id')
            print(f"  {message.get('message', '')}")
        
        if not topic_id:
            print(f"  ❌ Failed to create topic")
            return []
        
        # Get videos from database
        db = next(get_db())
        videos = get_videos_by_topic(db, topic_id)
        articles = get_articles_by_topic(db, topic_id)
        
        # Extract data
        video_data = []
        for i, video in enumerate(videos[:5], 1):  # Take first 5 videos
            video_dict = {
                'video_id': video.video_id,
                'topic': topic_name,
                'domain': domain,
                'title': video.title,
                'channel_title': video.channel_title,
                'transcript': video.transcript.text if video.transcript else '',
                'view_count': video.view_count,
                'like_count': video.like_count,
                'comment_count': video.comment_count,
                'duration': video.duration,
                'published_at': video.published_at.isoformat() if video.published_at else None,
                
                # Model predictions (will be replaced with open-source models later)
                'vader_sentiment': None,  # Placeholder
                'roberta_sentiment': None,
                'distilbert_sentiment': None,
                'emotions_json': video.emotions_json,
                
                # Ground truth (to be annotated manually)
                'ground_truth_sentiment': None,
                'ground_truth_emotions': None,
                'credibility_label': None,
                'misinformation_flag': None,
                
                # Metadata
                'annotation_date': None,
                'annotator': None,
                'collection_date': datetime.now().isoformat()
            }
            video_data.append(video_dict)
            print(f"  ✓ Video {i}/5: {video.title[:50]}...")
        
        # Store news articles for cross-platform analysis
        article_data = []
        for article in articles[:10]:  # Take first 10 articles
            article_dict = {
                'title': article.title,
                'source': article.source,
                'url': article.url,
                'published_at': article.published_at.isoformat() if article.published_at else None,
                'gemini_summary': article.gemini_justification,
                'relevance_score': article.relevance_score
            }
            article_data.append(article_dict)
        
        print(f"  ✅ Collected {len(video_data)} videos, {len(article_data)} articles")
        
        return {
            'videos': video_data,
            'articles': article_data
        }
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return {'videos': [], 'articles': []}

async def collect_all_data():
    """
    Collect data for all 25 topics.
    """
    all_data = {
        'metadata': {
            'collection_date': datetime.now().isoformat(),
            'total_topics': 25,
            'videos_per_topic': 5,
            'expected_total_videos': 125,
            'pipeline_version': 'ExplainNet v1.0'
        },
        'topics': []
    }
    
    topic_count = 0
    
    for domain, topics in RESEARCH_TOPICS.items():
        for topic in topics:
            topic_count += 1
            print(f"\n[{topic_count}/25] Processing...")
            
            data = await collect_videos_for_topic(topic, domain)
            
            all_data['topics'].append({
                'topic_name': topic,
                'domain': domain,
                'videos': data.get('videos', []),
                'articles': data.get('articles', [])
            })
            
            # Save incrementally (in case of crash)
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            
            # Respect API quotas - wait between topics
            if topic_count < 25:
                print(f"\n  ⏳ Waiting 60 seconds before next topic...")
                await asyncio.sleep(60)
    
    # Final summary
    total_videos = sum(len(t['videos']) for t in all_data['topics'])
    total_articles = sum(len(t['articles']) for t in all_data['topics'])
    
    print("\n" + "="*80)
    print("DATA COLLECTION COMPLETE")
    print("="*80)
    print(f"Topics collected: {len(all_data['topics'])}")
    print(f"Videos collected: {total_videos}")
    print(f"Articles collected: {total_articles}")
    print(f"Output file: {OUTPUT_FILE}")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(collect_all_data())
