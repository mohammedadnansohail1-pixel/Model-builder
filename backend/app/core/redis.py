"""Redis connection and utilities."""

from typing import Optional
import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import settings

# Global Redis connection
redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """
    Get Redis connection.

    Returns:
        Redis: Redis client instance
    """
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
        )
    return redis_client


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
