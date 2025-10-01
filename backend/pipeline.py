import os
import requests
from googleapiclient.discovery import build
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import time
import re
from textblob import TextBlob

load_dotenv()

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
NEWSAPI_ORG_KEY = os.getenv("NEWSAPI_ORG_KEY")

def calculate_content_relevance(content_text, topic_name, threshold=0.3):
    """
    Calculate relevance score between content and topic
    Returns True if content is relevant enough, False otherwise
    
    Research basis: Text similarity using keyword matching and semantic analysis
    Reference: "Information Retrieval: Implementing and Evaluating Search Engines" by Buttcher et al.
    """
    if not content_text or not topic_name:
        return False
    
    # Normalize text
    content_lower = content_text.lower()
    topic_lower = topic_name.lower()
    
    # Split topic into keywords
    topic_keywords = re.findall(r'\b\w+\b', topic_lower)
    
    # Calculate keyword match ratio
    keyword_matches = 0
    for keyword in topic_keywords:
        if len(keyword) > 2:  # Skip very short words
            if keyword in content_lower:
                keyword_matches += 1
    
    # Basic relevance score: percentage of topic keywords found
    if len(topic_keywords) > 0:
        relevance_score = keyword_matches / len(topic_keywords)
    else:
        relevance_score = 0
    
    # Additional semantic checks
    topic_phrases = topic_name.split()
    for phrase in topic_phrases:
        if len(phrase) > 3 and phrase.lower() in content_lower:
            relevance_score += 0.1  # Bonus for exact phrase matches
    
    print(f"    Relevance score: {relevance_score:.2f} (threshold: {threshold})")
    return relevance_score >= threshold

def filter_relevant_content(items, topic_name, content_field='title'):
    """Filter items based on content relevance to topic"""
    relevant_items = []
    
    for item in items:
        content_to_check = ""
        
        # Build content string from multiple fields for better matching
        if content_field == 'title' and 'title' in item:
            content_to_check += item['title'] + " "
        if 'description' in item:
            content_to_check += (item['description'] or "") + " "
        if 'headline' in item:
            content_to_check += (item['headline'] or "") + " "
        if 'full_text' in item:
            content_to_check += (item['full_text'] or "")[:500] + " "  # First 500 chars
        
        if calculate_content_relevance(content_to_check, topic_name):
            relevant_items.append(item)
        else:
            print(f"    Filtered out irrelevant content: {item.get('title', item.get('headline', 'Unknown'))[:50]}...")
    
    return relevant_items

def collect_guardian_data(topic_name, max_articles=20):
    """Collect Guardian articles with proper time intervals from earliest to latest"""
    print(f"Collecting HISTORICAL news from The Guardian for topic: {topic_name}")
    if not GUARDIAN_API_KEY: return []
    
    all_articles = []
    current_date = datetime.now()
    # Start from 2 years ago for development (reduced from 3 years)
    start_date = current_date - timedelta(days=730)  # 2 years
    
    # Collect in larger intervals to get 20 articles total
    # 3 time periods with specific article counts
    time_periods = [
        {'start_days': 730, 'end_days': 365, 'articles': 6, 'name': '2+ years ago'},    # 6 articles
        {'start_days': 365, 'end_days': 90, 'articles': 8, 'name': '1 year to 3 months ago'}, # 8 articles  
        {'start_days': 90, 'end_days': 0, 'articles': 6, 'name': 'Last 3 months'}       # 6 articles
    ]
    
    print(f"Searching from {start_date.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}")
    
    for period in time_periods:
        period_start = current_date - timedelta(days=period['start_days'])
        period_end = current_date - timedelta(days=period['end_days'])
        
        from_date = period_start.strftime('%Y-%m-%d')
        to_date = period_end.strftime('%Y-%m-%d')
        
        print(f"  Collecting {period['articles']} articles from {period['name']} ({from_date} to {to_date})")
        
        url = (f"https://content.guardianapis.com/search?"
               f"q={topic_name}&"
               f"from-date={from_date}&"
               f"to-date={to_date}&"
               f"api-key={GUARDIAN_API_KEY}&"
               f"page-size={period['articles']}&"
               f"order-by=oldest&"
               f"show-fields=all")
        
        try:
            data = requests.get(url).json()
            if 'response' in data and 'results' in data['response']:
                articles = []
                for i in data['response']['results']:
                    articles.append({
                        'headline': i.get('webTitle'),
                        'url': i.get('webUrl'),
                        'author': i.get('fields', {}).get('byline'),
                        'publication_date': i.get('webPublicationDate'),
                        'full_text': i.get('fields', {}).get('bodyText'),
                        'source_name': 'The Guardian',
                        'data_source_api': 'Guardian',
                        'country': 'GB',
                        'language': 'en',
                        'time_period': period['name']
                    })
                all_articles.extend(articles)
                print(f"    Found {len(articles)} articles in {period['name']}")
            
            # Rate limiting - Guardian allows 12 requests per second
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error fetching Guardian data for period {period['name']}: {e}")
    
    # Filter for relevance before returning
    print(f"  Filtering {len(all_articles)} articles for relevance...")
    relevant_articles = filter_relevant_content(all_articles, topic_name, 'headline')
    
    print(f"Total Guardian articles collected: {len(relevant_articles)} (filtered from {len(all_articles)})")
    return relevant_articles[:max_articles]  # Limit total results

def collect_newsapi_org_data(topic_name, max_articles=10):
    """Collect recent news articles by topic with time intervals"""
    print(f"Collecting RECENT news from NewsAPI.org for topic: {topic_name}")
    if not NEWSAPI_ORG_KEY: return []
    
    all_articles = []
    current_date = datetime.now()
    # NewsAPI free plan only allows last 30 days, so we'll collect recent data
    start_date = current_date - timedelta(days=30)
    
    # Collect in 2 time periods for development (reduced from 4)
    time_periods = [
        {'start_days': 30, 'end_days': 15, 'articles': 5, 'name': 'Weeks 3-4 ago'},  # 5 articles
        {'start_days': 15, 'end_days': 0, 'articles': 5, 'name': 'Last 2 weeks'}     # 5 articles
    ]
    
    print(f"Searching recent news from {start_date.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}")
    
    for period in time_periods:
        period_start = current_date - timedelta(days=period['start_days'])
        period_end = current_date - timedelta(days=period['end_days'])
        
        from_date = period_start.strftime('%Y-%m-%d')
        to_date = period_end.strftime('%Y-%m-%d')
        
        print(f"  Collecting {period['articles']} articles from {period['name']} ({from_date} to {to_date})")
        
        # Use everything endpoint to search by topic with date range
        url = (f"https://newsapi.org/v2/everything?"
               f"q={topic_name}&"
               f"from={from_date}&"
               f"to={to_date}&"
               f"sortBy=publishedAt&"
               f"language=en&"
               f"apiKey={NEWSAPI_ORG_KEY}&"
               f"pageSize={period['articles']}")
        
        try:
            data = requests.get(url).json()
            if 'articles' in data:
                articles = []
                for i in data['articles']:
                    # Skip articles without proper content
                    if not i.get('title') or i.get('title') == '[Removed]':
                        continue
                    
                    articles.append({
                        'headline': i.get('title'),
                        'url': i.get('url'),
                        'author': i.get('author'),
                        'publication_date': i.get('publishedAt'),
                        'full_text': i.get('content') or i.get('description'),
                        'source_name': i.get('source', {}).get('name'),
                        'data_source_api': 'NewsAPI.org',
                        'country': 'global',
                        'language': 'en',
                        'time_period': period['name']
                    })
                all_articles.extend(articles)
                print(f"    Found {len(articles)} articles in {period['name']}")
            
            # Rate limiting - NewsAPI allows 1000 requests per day
            time.sleep(0.2)
            
        except Exception as e:
            print(f"Error fetching NewsAPI data for period {period['name']}: {e}")
    
    # Filter for relevance before returning
    print(f"  Filtering {len(all_articles)} articles for relevance...")
    relevant_articles = filter_relevant_content(all_articles, topic_name, 'headline')
    
    print(f"Total NewsAPI articles collected: {len(relevant_articles)} (filtered from {len(all_articles)})")
    return relevant_articles[:max_articles]

def collect_youtube_data(topic_name, max_videos=10, max_comments=5):
    """Collect YouTube videos with proper time intervals from oldest to newest"""
    print(f"Collecting YouTube data for topic: {topic_name}")
    if not YOUTUBE_API_KEY: return []
    
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    all_videos = []
    
    # Define time periods to search (YouTube allows date filtering)
    current_date = datetime.now()
    
    # Search in different time periods to get historical progression
    # Reduced for development - total 10 videos distributed across time
    time_periods = [
        {'name': '2+ years ago', 'days_back': (730, 1095), 'max_results': 2},  # 2 videos
        {'name': '1-2 years ago', 'days_back': (365, 730), 'max_results': 2},  # 2 videos
        {'name': '6-12 months ago', 'days_back': (180, 365), 'max_results': 2}, # 2 videos
        {'name': '3-6 months ago', 'days_back': (90, 180), 'max_results': 2},   # 2 videos
        {'name': '1-3 months ago', 'days_back': (30, 90), 'max_results': 1},    # 1 video
        {'name': 'Last month', 'days_back': (0, 30), 'max_results': 1}          # 1 video
    ]
    
    for period in time_periods:
        print(f"  Collecting videos from: {period['name']}")
        
        # Calculate date range
        published_after = (current_date - timedelta(days=period['days_back'][1])).isoformat() + 'Z'
        published_before = (current_date - timedelta(days=period['days_back'][0])).isoformat() + 'Z'
        
        try:
            # Search with date filtering
            search_response = youtube.search().list(
                q=topic_name,
                part='snippet',
                maxResults=period['max_results'],
                type='video',
                order='date',  # Sort by upload date
                publishedAfter=published_after,
                publishedBefore=published_before
            ).execute()
            
            video_ids = [i['id']['videoId'] for i in search_response.get('items', [])]
            if not video_ids:
                print(f"    No videos found for {period['name']}")
                continue
            
            # Get detailed video information
            video_details = youtube.videos().list(
                part="snippet,statistics",
                id=",".join(video_ids)
            ).execute()
            
            period_videos = []
            for item in video_details.get('items', []):
                video_data = {
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'publication_date': item['snippet']['publishedAt'],
                    'description': item['snippet']['description'],
                    'channel_name': item['snippet']['channelTitle'],
                    'view_count': item.get('statistics', {}).get('viewCount'),
                    'like_count': item.get('statistics', {}).get('likeCount'),
                    'comment_count': item.get('statistics', {}).get('commentCount'),
                    'time_period': period['name'],
                    'comments': []
                }
                
                # Collect comments if available
                if max_comments > 0 and item.get('statistics', {}).get('commentCount', '0') != '0':
                    try:
                        comments = youtube.commentThreads().list(
                            part="snippet",
                            videoId=item['id'],
                            maxResults=max_comments,
                            textFormat="plainText"
                        ).execute()
                        
                        for c_item in comments.get('items', []):
                            c = c_item['snippet']['topLevelComment']['snippet']
                            video_data['comments'].append({
                                'comment_id': c_item['id'],
                                'comment_text': c['textDisplay'],
                                'author_name': c['authorDisplayName'],
                                'publication_date': c['publishedAt'],
                                'like_count': c['likeCount']
                            })
                    except Exception as e:
                        print(f"    Could not fetch comments for video {item['id']}: {e}")
                
                period_videos.append(video_data)
            
            all_videos.extend(period_videos)
            print(f"    Found {len(period_videos)} videos in {period['name']}")
            
            # Rate limiting for YouTube API
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error fetching YouTube data for {period['name']}: {e}")
    
    # Sort all videos by publication date (oldest first)
    all_videos.sort(key=lambda x: x['publication_date'])
    
    # Filter for relevance before returning
    print(f"  Filtering {len(all_videos)} videos for relevance...")
    relevant_videos = filter_relevant_content(all_videos, topic_name, 'title')
    
    print(f"Total YouTube videos collected: {len(relevant_videos)} (filtered from {len(all_videos)})")
    return relevant_videos[:max_videos]