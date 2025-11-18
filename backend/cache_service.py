"""
In-Memory Cache Service for ExplainNet
Provides TTL-based caching for topics and search results
"""

import time
import threading
from typing import Optional, Dict, Any
from datetime import datetime


class InMemoryCache:
    """Simple in-memory cache with TTL (Time To Live) support"""
    
    def __init__(self):
        self._cache: Dict[str, tuple] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if exists and not expired
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry_time = self._cache[key]
            
            # Check if expired
            if time.time() > expiry_time:
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any, ttl_seconds: int = 900):
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default: 900 = 15 minutes)
        """
        with self._lock:
            expiry_time = time.time() + ttl_seconds
            self._cache[key] = (value, expiry_time)
    
    def delete(self, key: str):
        """Delete a specific key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_entries = len(self._cache)
            
            # Count expired entries
            current_time = time.time()
            expired = sum(1 for _, expiry in self._cache.values() if current_time > expiry)
            active = total_entries - expired
            
            # Calculate total size (approximate)
            import sys
            total_size_bytes = sum(
                sys.getsizeof(k) + sys.getsizeof(v[0])
                for k, v in self._cache.items()
            )
            
            return {
                "total_entries": total_entries,
                "active_entries": active,
                "expired_entries": expired,
                "size_bytes": total_size_bytes,
                "size_mb": round(total_size_bytes / (1024 * 1024), 2)
            }
    
    def cleanup_expired(self):
        """Remove expired entries from cache"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self._cache.items()
                if current_time > expiry
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)


# Global cache instance
_cache_instance = InMemoryCache()


def get_cache() -> InMemoryCache:
    """Get the global cache instance"""
    return _cache_instance


# Cache key generators
def topic_search_key(topic_name: str) -> str:
    """Generate cache key for topic search results"""
    return f"topic_search:{topic_name.lower().strip()}"


def video_analysis_key(video_id: str) -> str:
    """Generate cache key for video analysis"""
    return f"video_analysis:{video_id}"


def topic_full_analysis_key(topic_id: int) -> str:
    """Generate cache key for complete topic analysis"""
    return f"topic_full:{topic_id}"


# High-level cache functions
def get_cached(key: str) -> Optional[Any]:
    """Generic get from cache"""
    cache = get_cache()
    return cache.get(key)


def set_cached(key: str, value: Any, ttl: int = 900):
    """Generic set to cache"""
    cache = get_cache()
    cache.set(key, value, ttl)


def cache_topic_search(topic_name: str, result: Dict, ttl_seconds: int = 900):
    """Cache topic search results (15 min default)"""
    cache = get_cache()
    key = topic_search_key(topic_name)
    cache.set(key, result, ttl_seconds)
    print(f"💾 Cached topic search: {topic_name} (TTL: {ttl_seconds}s)")


def get_cached_topic_search(topic_name: str) -> Optional[Dict]:
    """Get cached topic search results"""
    cache = get_cache()
    key = topic_search_key(topic_name)
    result = cache.get(key)
    if result:
        print(f"💾 CACHE HIT: Topic search '{topic_name}' (instant!)")
    return result


def cache_video_analysis(video_id: str, result: Dict, ttl_seconds: int = 3600):
    """Cache video analysis (1 hour default - videos don't change)"""
    cache = get_cache()
    key = video_analysis_key(video_id)
    cache.set(key, result, ttl_seconds)


def get_cached_video_analysis(video_id: str) -> Optional[Dict]:
    """Get cached video analysis"""
    cache = get_cache()
    key = video_analysis_key(video_id)
    return cache.get(key)


def invalidate_topic_cache(topic_name: str):
    """Invalidate cache for a specific topic"""
    cache = get_cache()
    key = topic_search_key(topic_name)
    cache.delete(key)
    print(f"🗑️  Invalidated cache for topic: {topic_name}")


def clear_all_cache():
    """Clear entire cache"""
    cache = get_cache()
    cache.clear()
    print("🗑️  All cache cleared!")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    cache = get_cache()
    return cache.get_stats()
