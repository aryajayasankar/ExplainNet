import aiohttp
import asyncio
import os
import html
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_BASE_URL = "https://www.googleapis.com/youtube/v3"


def parse_iso8601_duration(duration: str) -> Tuple[int, float]:
    """
    Parse ISO 8601 duration format (PT1H2M10S) to seconds and minutes
    
    Examples:
        PT15M33S -> (933, 15.55)
        PT1H2M10S -> (3730, 62.17)
        PT45S -> (45, 0.75)
    
    Returns:
        Tuple of (total_seconds, total_minutes)
    """
    if not duration:
        return (0, 0.0)
    
    # Pattern: PT(hours)H(minutes)M(seconds)S
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration)
    
    if not match:
        return (0, 0.0)
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    total_seconds = hours * 3600 + minutes * 60 + seconds
    total_minutes = total_seconds / 60.0
    
    return (total_seconds, total_minutes)


def is_valid_video(duration_minutes: float, language: Optional[str] = None, max_minutes: int = 35) -> bool:
    """
    Check if video meets filtering criteria
    
    Args:
        duration_minutes: Video duration in minutes
        language: Video language code (e.g., 'en', 'hi')
        max_minutes: Maximum allowed duration (default 35 minutes)
    
    Returns:
        True if video is valid (English and ≤ max_minutes)
    """
    # Duration check
    if duration_minutes <= 0 or duration_minutes > max_minutes:
        return False
    
    # Language check (English only, or assume English if not specified)
    if language and language.lower() not in ['en', 'en-us', 'en-gb', 'en-ca', 'en-au']:
        return False
    
    return True


def parse_youtube_datetime(date_str: str) -> datetime:
    """Convert YouTube ISO 8601 datetime string to Python datetime object"""
    if not date_str:
        return datetime.now()
    try:
        # YouTube returns ISO 8601 format like "2024-11-09T10:30:00Z"
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        return datetime.now()


async def search_videos(topic: str, max_results: int = 50, target_valid_videos: int = 10) -> List[Dict]:
    """
    Search for videos related to a topic using YouTube Data API
    Filters for English videos ≤35 minutes
    
    Args:
        topic: Search query
        max_results: Maximum videos to fetch from API
        target_valid_videos: Target number of valid videos to return (default 10)
    
    Returns:
        List of valid videos (up to target_valid_videos)
    """
    
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY not found in environment variables")
    
    params = {
        "part": "snippet",
        "q": topic,
        "type": "video",
        "maxResults": max_results,
        "order": "relevance",
        "videoDuration": "medium",  # 4-20 minutes (helps filter out very long videos)
        "relevanceLanguage": "en",  # Prefer English results
        "key": YOUTUBE_API_KEY
    }
    
    # Retry logic for network issues using aiohttp
    max_retries = 3
    timeout = aiohttp.ClientTimeout(total=30)
    data = None
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{YOUTUBE_BASE_URL}/search", params=params) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    break
        except (aiohttp.ClientConnectorError, aiohttp.ClientResponseError, asyncio.TimeoutError) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"⚠️  YouTube API connection attempt {attempt + 1} failed, retrying in {wait_time}s...")
                import asyncio
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ YouTube API connection failed after {max_retries} attempts: {e}")
                raise
    
    videos = []
    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]
        
        videos.append({
            "video_id": video_id,
            "title": html.unescape(snippet.get("title", "")),
            "channel_name": html.unescape(snippet.get("channelTitle", "")),
            "channel_id": snippet.get("channelId", ""),
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "published_at": parse_youtube_datetime(snippet.get("publishedAt", "")),
            "language": snippet.get("defaultAudioLanguage") or snippet.get("defaultLanguage") or "en"
        })
    
    return videos


async def get_video_details(video_ids: List[str]) -> List[Dict]:
    """Get detailed statistics and content details for videos"""
    
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY not found in environment variables")
    
    # YouTube API allows max 50 video IDs per request
    video_ids_str = ",".join(video_ids[:50])
    
    params = {
        "part": "statistics,contentDetails,snippet",
        "id": video_ids_str,
        "key": YOUTUBE_API_KEY
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(f"{YOUTUBE_BASE_URL}/videos", params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
    
    videos_details = []
    for item in data.get("items", []):
        stats = item.get("statistics", {})
        content_details = item.get("contentDetails", {})
        snippet = item.get("snippet", {})
        
        # Parse duration
        duration_iso = content_details.get("duration", "")
        duration_seconds, duration_minutes = parse_iso8601_duration(duration_iso)
        
        # Get language
        language = snippet.get("defaultAudioLanguage") or snippet.get("defaultLanguage") or "en"
        
        videos_details.append({
            "video_id": item["id"],
            "view_count": int(stats.get("viewCount", 0)),
            "like_count": int(stats.get("likeCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "duration": duration_iso,
            "duration_seconds": duration_seconds,
            "duration_minutes": round(duration_minutes, 2),
            "language": language,
            "is_valid": is_valid_video(duration_minutes, language)
        })
    
    return videos_details


async def get_channel_details(channel_ids: List[str]) -> List[Dict]:
    """Get channel subscriber counts"""
    
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY not found in environment variables")
    
    channel_ids_str = ",".join(channel_ids[:50])
    
    params = {
        "part": "statistics",
        "id": channel_ids_str,
        "key": YOUTUBE_API_KEY
    }
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(f"{YOUTUBE_BASE_URL}/channels", params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
    
    channels = []
    for item in data.get("items", []):
        stats = item.get("statistics", {})
        
        channels.append({
            "channel_id": item["id"],
            "subscriber_count": int(stats.get("subscriberCount", 0))
        })
    
    return channels


async def get_video_comments(video_id: str, max_results: int = 20) -> List[Dict]:
    """
    Get comments for a video
    
    Args:
        video_id: YouTube video ID
        max_results: Maximum number of comments (default 20)
    
    Returns:
        List of comment dictionaries
    """
    
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY not found in environment variables")
    
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": min(max_results, 20),  # API limit is 100, we want 20
        "order": "relevance",  # Get most relevant/popular comments
        "textFormat": "plainText",
        "key": YOUTUBE_API_KEY
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{YOUTUBE_BASE_URL}/commentThreads", params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
        
        comments = []
        for item in data.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            
            comments.append({
                "comment_id": item["id"],
                "author": snippet.get("authorDisplayName", ""),
                "text": snippet.get("textDisplay", ""),
                "like_count": int(snippet.get("likeCount", 0)),
                "published_at": parse_youtube_datetime(snippet.get("publishedAt", ""))
            })
        
        return comments
    
    except httpx.HTTPStatusError as e:
        # Comments might be disabled
        if e.response.status_code == 403:
            return []
        raise
