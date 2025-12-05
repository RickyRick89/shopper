"""Caching utilities for search and frequently accessed data."""

import json
import redis
from typing import Optional, Any, Callable
from functools import wraps

from app.core.config import get_settings

settings = get_settings()

# Initialize Redis connection
redis_client = Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(settings.redis_url)
            # Test connection
            redis_client.ping()
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            redis_client = None
    return redis_client


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments."""
    key_parts = [str(arg) for arg in args if arg is not None]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None])
    return ":".join(key_parts)


def cached(ttl_seconds: int = 3600):
    """Decorator to cache function results in Redis.
    
    Args:
        ttl_seconds: Time to live in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            redis_conn = get_redis_client()
            
            if redis_conn is None:
                # If Redis is not available, just call the function
                return func(*args, **kwargs)
            
            # Generate cache key
            func_name = func.__name__
            key = f"{func_name}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            try:
                cached_result = redis_conn.get(key)
                if cached_result:
                    return json.loads(cached_result)
            except Exception as e:
                print(f"Cache retrieval error: {e}")
            
            # Call function and cache result
            result = func(*args, **kwargs)
            
            try:
                redis_conn.setex(
                    key,
                    ttl_seconds,
                    json.dumps(result, default=str)
                )
            except Exception as e:
                print(f"Cache storage error: {e}")
            
            return result
        
        return wrapper
    return decorator


def clear_cache_pattern(pattern: str) -> None:
    """Clear cache entries matching a pattern."""
    redis_conn = get_redis_client()
    if redis_conn is None:
        return
    
    try:
        keys = redis_conn.keys(pattern)
        if keys:
            redis_conn.delete(*keys)
    except Exception as e:
        print(f"Error clearing cache: {e}")


def clear_search_cache() -> None:
    """Clear all search-related cache entries."""
    clear_cache_pattern("search_products*")
    clear_cache_pattern("get_search_suggestions*")
    clear_cache_pattern("get_deals*")
