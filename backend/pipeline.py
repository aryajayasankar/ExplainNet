import os
import requests
from googleapiclient.discovery import build
from dotenv import load_dotenv
import json

load_dotenv()

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
NEWSAPI_ORG_KEY = os.getenv("NEWSAPI_ORG_KEY")

def collect_guardian_data(topic_name, max_articles=100):
    print(f"Collecting HISTORICAL news from The Guardian for topic: {topic_name}")
    if not GUARDIAN_API_KEY: return []
    url = f"https://content.guardianapis.com/search?q={topic_name}&api-key={GUARDIAN_API_KEY}&page-size={max_articles}&show-fields=all"
    try:
        data = requests.get(url).json()
        articles = [{'headline': i.get('webTitle'), 'url': i.get('webUrl'), 'author': i.get('fields', {}).get('byline'),'publication_date': i.get('webPublicationDate'), 'full_text': i.get('fields', {}).get('bodyText'),'source_name': 'The Guardian', 'data_source_api': 'Guardian', 'country': 'GB', 'language': 'en'} for i in data['response']['results']]
        print(f"Collected {len(articles)} articles from The Guardian.")
        return articles
    except Exception as e:
        print(f"Error fetching Guardian data: {e}")
        return []

def collect_newsapi_org_data(country='us', max_articles=50):
    print(f"Collecting RECENT top headlines from NewsAPI.org for country: {country}")
    if not NEWSAPI_ORG_KEY: return []
    url = f"https://newsapi.org/v2/top-headlines?country={country}&apiKey={NEWSAPI_ORG_KEY}&pageSize={max_articles}"
    try:
        data = requests.get(url).json()
        articles = [{'headline': i.get('title'), 'url': i.get('url'), 'author': i.get('author'),'publication_date': i.get('publishedAt'), 'full_text': i.get('content') or i.get('description'),'source_name': i.get('source', {}).get('name'), 'data_source_api': 'NewsAPI.org', 'country': country, 'language': 'en'} for i in data.get('articles', [])]
        print(f"Collected {len(articles)} articles from NewsAPI.org.")
        return articles
    except Exception as e:
        print(f"Error fetching NewsAPI.org data: {e}")
        return []

def collect_youtube_data(topic_name, max_videos=15, max_comments=25):
    print(f"Collecting YouTube data for topic: {topic_name}")
    if not YOUTUBE_API_KEY: return []
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    videos_list = []
    try:
        search_response = youtube.search().list(q=topic_name, part='snippet', maxResults=max_videos, type='video').execute()
        video_ids = [i['id']['videoId'] for i in search_response.get('items', [])]
        if not video_ids: return []
        video_details = youtube.videos().list(part="snippet,statistics", id=",".join(video_ids)).execute()
        for item in video_details.get('items', []):
            video_data = {'video_id': item['id'], 'title': item['snippet']['title'], 'publication_date': item['snippet']['publishedAt'], 'description': item['snippet']['description'], 'channel_name': item['snippet']['channelTitle'], 'view_count': item.get('statistics', {}).get('viewCount'), 'like_count': item.get('statistics', {}).get('likeCount'), 'comment_count': item.get('statistics', {}).get('commentCount'), 'comments': []}
            if max_comments > 0 and item.get('statistics', {}).get('commentCount', '0') != '0':
                try:
                    comments = youtube.commentThreads().list(part="snippet", videoId=item['id'], maxResults=max_comments, textFormat="plainText").execute()
                    for c_item in comments.get('items', []):
                        c = c_item['snippet']['topLevelComment']['snippet']
                        video_data['comments'].append({'comment_id': c_item['id'], 'comment_text': c['textDisplay'], 'author_name': c['authorDisplayName'], 'publication_date': c['publishedAt'], 'like_count': c['likeCount']})
                except Exception: pass
            videos_list.append(video_data)
        print(f"Collected data for {len(videos_list)} videos.")
        return videos_list
    except Exception as e:
        print(f"An error with YouTube API: {e}")
        return []