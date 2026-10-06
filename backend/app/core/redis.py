"""Redis caching and distributed coordination abstraction for Dhruva.AI.

CRITICAL INVARIANT: Redis is strictly an acceleration and coordination layer.
It NEVER acts as the primary source of academic truth. If Redis is unavailable or
times out, the system degrades gracefully and falls back to in-memory/database operations.
"""

import json
from typing import Optional, Any
from app.core.config import settings
from app.core.logging import logger


class RedisManager:
    """Manages Redis connection lifecycle and graceful fallbacks."""

    def __init__(self):
        self._client = None
        self._is_connected = False
        self._in_memory_cache = {}

    async def initialize(self) -> None:
        """Initializes Redis client if enabled."""
        if not settings.REDIS_ENABLED:
            logger.info("Redis is disabled by configuration. Operating in graceful fallback mode.")
            return

        try:
            # We use redis.asyncio if installed, otherwise log graceful fallback
            import redis.asyncio as aioredis  # type: ignore

            self._client = aioredis.from_url(
                settings.REDIS_URL,
                socket_timeout=settings.REDIS_TIMEOUT_SECONDS,
                decode_responses=True,
            )
            await self._client.ping()
            self._is_connected = True
            logger.info("Connected to Redis distributed coordinator.")
        except Exception as exc:
            logger.warning(
                f"Redis unavailable ({exc}). Operating in graceful fallback mode without distributed caching."
            )
            self._is_connected = False

    async def get(self, key: str) -> Optional[str]:
        """Retrieves a cached value, degrading gracefully if Redis is down."""
        if self._is_connected and self._client:
            try:
                return await self._client.get(key)
            except Exception as e:
                logger.warning(f"Redis get failed for key '{key}': {e}")
        return self._in_memory_cache.get(key)

    async def set(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        """Stores a cached value with optional expiration."""
        if self._is_connected and self._client:
            try:
                await self._client.set(key, value, ex=expire_seconds)
                return True
            except Exception as e:
                logger.warning(f"Redis set failed for key '{key}': {e}")
        self._in_memory_cache[key] = value
        return True

    async def delete(self, key: str) -> bool:
        """Deletes a key from cache."""
        if self._is_connected and self._client:
            try:
                await self._client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete failed for key '{key}': {e}")
        self._in_memory_cache.pop(key, None)
        return True

    async def health_check(self) -> dict:
        """Evaluates Redis connectivity status."""
        if not settings.REDIS_ENABLED:
            return {
                "status": "disabled",
                "connected": False,
                "mode": "in-memory-fallback",
            }

        if self._is_connected and self._client:
            try:
                await self._client.ping()
                return {"status": "healthy", "connected": True}
            except Exception as e:
                return {"status": "degraded", "connected": False, "error": str(e)}

        return {"status": "disconnected", "connected": False, "mode": "in-memory-fallback"}

    async def close(self) -> None:
        """Closes connection gracefully on shutdown."""
        if self._client:
            try:
                await self._client.close()
            except Exception:
                pass
            self._is_connected = False


redis_manager = RedisManager()
