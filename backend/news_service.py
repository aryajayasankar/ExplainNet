import aiohttp
import asyncio
import os
from typing import List, Dict
from datetime import datetime, timedelta

NEWS_API_KEY = os.getenv("NEWSAPI_ORG_KEY")
GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"
GUARDIAN_API_URL = "https://content.guardianapis.com/search"


def parse_news_datetime(date_str: str) -> datetime:
    """Convert News API ISO datetime string to Python datetime object"""
    if not date_str:
        return datetime.now()
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        return datetime.now()


async def search_articles(topic: str, max_results: int = 25) -> List[Dict]:
    """Search for news articles related to a topic with error handling and bypass"""
    
    if not NEWS_API_KEY:
        print("⚠️  NEWSAPI_ORG_KEY not found - skipping NewsAPI search")
        return []
    
    try:
        # Get articles from the last 30 days
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        params = {
            "q": topic,
            "apiKey": NEWS_API_KEY,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": max_results,
            "from": from_date
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(NEWS_API_URL, params=params) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"⚠️  NewsAPI returned {resp.status}: {error_text[:200]}")
                    print("   Bypassing NewsAPI and continuing...")
                    return []
                
                data = await resp.json()
        
        articles = []
        for item in data.get("articles", []):
            articles.append({
                "title": item.get("title", ""),
                "source": item.get("source", {}).get("name", ""),
                "source_type": "recent",
                "author": item.get("author", ""),
                "url": item.get("url", ""),
                "published_at": parse_news_datetime(item.get("publishedAt", "")),
                "description": item.get("description", ""),
                "content": item.get("content", "")
            })
        
        return articles
    
    except aiohttp.ClientResponseError as e:
        print(f"⚠️  NewsAPI HTTP error {e.status}: {str(e)[:200]}")
        print("   Bypassing NewsAPI and continuing...")
        return []
    except aiohttp.ClientConnectorError as e:
        print(f"⚠️  NewsAPI connection error: {str(e)[:200]}")
        print("   Bypassing NewsAPI and continuing...")
        return []
    except asyncio.TimeoutError:
        print("⚠️  NewsAPI timeout after 30s")
        print("   Bypassing NewsAPI and continuing...")
        return []
    except Exception as e:
        print(f"⚠️  NewsAPI unexpected error: {type(e).__name__}: {str(e)[:200]}")
        print("   Bypassing NewsAPI and continuing...")
        return []


async def search_guardian_articles(topic: str, max_results: int = 25) -> List[Dict]:
    """Search for historical articles from The Guardian with comprehensive error handling"""
    
    if not GUARDIAN_API_KEY:
        print("⚠️  GUARDIAN_API_KEY not found - skipping Guardian search")
        return []
    
    try:
        # Get historical articles (older than 30 days)
        to_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        params = {
            "q": topic,
            "api-key": GUARDIAN_API_KEY,
            "page-size": max_results,
            "from-date": from_date,
            "to-date": to_date,
            "show-fields": "byline,trailText,body",
            "order-by": "relevance"
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(GUARDIAN_API_URL, params=params) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"⚠️  Guardian API returned {resp.status}: {error_text[:200]}")
                    print("   Bypassing Guardian and continuing...")
                    return []
                
                data = await resp.json()
        
        articles = []
        for item in data.get("response", {}).get("results", []):
            articles.append({
                "title": item.get("webTitle", ""),
                "source": "The Guardian",
                "source_type": "historical",
                "author": item.get("fields", {}).get("byline", ""),
                "url": item.get("webUrl", ""),
                "published_at": parse_news_datetime(item.get("webPublicationDate", "")),
                "description": item.get("fields", {}).get("trailText", ""),
                "content": item.get("fields", {}).get("body", "")[:500]  # Limit content
            })
        
        return articles
    
    except aiohttp.ClientResponseError as e:
        print(f"⚠️  Guardian HTTP error {e.status}: {str(e)[:200]}")
        print("   Bypassing Guardian and continuing...")
        return []
    except aiohttp.ClientConnectorError as e:
        print(f"⚠️  Guardian connection error: {str(e)[:200]}")
        print("   Bypassing Guardian and continuing...")
        return []
    except asyncio.TimeoutError:
        print("⚠️  Guardian timeout after 30s")
        print("   Bypassing Guardian and continuing...")
        return []
    except Exception as e:
        print(f"⚠️  Guardian unexpected error: {type(e).__name__}: {str(e)[:200]}")
        print("   Bypassing Guardian and continuing...")
        return []
