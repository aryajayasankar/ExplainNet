import os
import requests
from googleapiclient.discovery import build
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def collect_news_data(topic_name, max_articles=100):
    """Fetches news articles from The Guardian API for a given topic."""
    print(f"Collecting news data for topic: {topic_name}")
    if not GUARDIAN_API_KEY:
        print("Guardian API key not found.")
        return []

    search_url = f"https://content.guardianapis.com/search?q={topic_name}&api-key={GUARDIAN_API_KEY}&page-size={max_articles}&show-fields=all"

    try:
        response = requests.get(search_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        articles_list = []
        for item in data['response']['results']:
            articles_list.append({
                'headline': item.get('webTitle'),
                'url': item.get('webUrl'),
                'publication_date': item.get('webPublicationDate'),
                'full_text': item.get('fields', {}).get('bodyText'),
                'source_name': 'The Guardian'
            })
        print(f"Collected {len(articles_list)} articles.")
        return articles_list
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news data: {e}")
        return []


def collect_youtube_data(topic_name, max_videos=15, max_comments=25):
    """Fetches YouTube videos and comments for a given topic."""
    print(f"Collecting YouTube data for topic: {topic_name}")
    if not YOUTUBE_API_KEY:
        print("YouTube API key not found.")
        return []

    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    videos_list = []
    try:
        # 1. Search for videos
        search_request = youtube.search().list(
            q=topic_name,
            part='snippet',
            maxResults=max_videos,
            type='video'
        )
        search_response = search_request.execute()

        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

        if not video_ids:
            print("No videos found.")
            return []

        # 2. Get video details (view count, like count etc.)
        video_details_request = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(video_ids)
        )
        video_details_response = video_details_request.execute()

        for item in video_details_response.get('items', []):
            video_data = {
                'video_id': item['id'],
                'title': item['snippet']['title'],
                'publication_date': item['snippet']['publishedAt'],
                'description': item['snippet']['description'],
                'channel_name': item['snippet']['channelTitle'],
                'view_count': item.get('statistics', {}).get('viewCount'),
                'like_count': item.get('statistics', {}).get('likeCount'),
                'comment_count': item.get('statistics', {}).get('commentCount'),
                'comments': []
            }

            # 3. Get comments for each video
            if max_comments > 0 and item.get('statistics', {}).get('commentCount', '0') != '0':
                try:
                    comment_request = youtube.commentThreads().list(
                        part="snippet",
                        videoId=item['id'],
                        maxResults=max_comments,
                        textFormat="plainText"
                    )
                    comment_response = comment_request.execute()

                    for comment_item in comment_response.get('items', []):
                        comment = comment_item['snippet']['topLevelComment']['snippet']
                        video_data['comments'].append({
                            'comment_id': comment_item['id'],
                            'comment_text': comment['textDisplay'],
                            'author_name': comment['authorDisplayName'],
                            'publication_date': comment['publishedAt'],
                            'like_count': comment['likeCount']
                        })
                except Exception as e:
                    # Sometimes comments are disabled, so we just skip
                    print(f"Could not fetch comments for video {item['id']}: {e}")

            videos_list.append(video_data)

        print(f"Collected data for {len(videos_list)} videos.")
        return videos_list

    except Exception as e:
        print(f"An error occurred with the YouTube API: {e}")
        return []


# This block allows us to test the functions by running the file directly
if __name__ == '__main__':
    test_topic = "latest AI developments"

    # Test News Collection
    news = collect_news_data(test_topic, max_articles=5)
    print("\n--- News Test Results ---")
    # Print the headline of the first article if it exists
    if news:
        print(json.dumps(news[0], indent=2))

    # Test YouTube Collection
    videos = collect_youtube_data(test_topic, max_videos=2, max_comments=3)
    print("\n--- YouTube Test Results ---")
    # Print the title of the first video if it exists
    if videos:
        print(json.dumps(videos[0], indent=2))