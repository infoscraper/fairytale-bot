"""
Redis configuration and connection
"""
import redis.asyncio as redis
from .config import settings

# Global Redis connection
_redis_client = None


async def get_redis() -> redis.Redis:
    """Get Redis connection"""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    
    if _redis_client:
        # Handle both Redis 4.x and 5.x versions
        if hasattr(_redis_client, 'aclose'):
            await _redis_client.aclose()
        else:
            await _redis_client.close()
        _redis_client = None
