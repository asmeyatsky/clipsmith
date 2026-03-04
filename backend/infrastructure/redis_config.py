"""
Redis configuration module for Clipsmith.

Provides a configurable Redis connection with automatic fallback
to in-memory storage for local development when Redis is unavailable.
"""

import os
import time
import logging
import threading
from typing import Optional, Any

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Simple in-memory cache that mimics basic Redis operations.
    Used as a fallback when Redis is not available in development."""

    def __init__(self):
        self._store: dict = {}
        self._expiry: dict = {}
        self._lock = threading.Lock()

    def _cleanup_expired(self):
        """Remove expired keys."""
        now = time.time()
        expired_keys = [
            k for k, exp in self._expiry.items() if exp and exp < now
        ]
        for k in expired_keys:
            self._store.pop(k, None)
            self._expiry.pop(k, None)

    def get(self, key: str) -> Optional[bytes]:
        with self._lock:
            self._cleanup_expired()
            value = self._store.get(key)
            if value is None:
                return None
            return value.encode() if isinstance(value, str) else value

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        with self._lock:
            self._store[key] = value if isinstance(value, str) else str(value)
            if ex:
                self._expiry[key] = time.time() + ex
            else:
                self._expiry[key] = None
            return True

    def setex(self, key: str, seconds: int, value: Any) -> bool:
        return self.set(key, value, ex=seconds)

    def delete(self, *keys: str) -> int:
        count = 0
        with self._lock:
            for key in keys:
                if key in self._store:
                    del self._store[key]
                    self._expiry.pop(key, None)
                    count += 1
        return count

    def exists(self, key: str) -> bool:
        with self._lock:
            self._cleanup_expired()
            return key in self._store

    def incr(self, key: str) -> int:
        with self._lock:
            self._cleanup_expired()
            current = int(self._store.get(key, 0))
            current += 1
            self._store[key] = str(current)
            return current

    def expire(self, key: str, seconds: int) -> bool:
        with self._lock:
            if key in self._store:
                self._expiry[key] = time.time() + seconds
                return True
            return False

    def ttl(self, key: str) -> int:
        with self._lock:
            exp = self._expiry.get(key)
            if exp is None:
                return -1 if key in self._store else -2
            remaining = exp - time.time()
            if remaining <= 0:
                self._store.pop(key, None)
                self._expiry.pop(key, None)
                return -2
            return int(remaining)

    def ping(self) -> bool:
        return True

    def flushdb(self) -> bool:
        with self._lock:
            self._store.clear()
            self._expiry.clear()
        return True


def _parse_redis_url(url: str) -> dict:
    """Parse a Redis URL into connection parameters."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 6379,
        "db": int(parsed.path.lstrip("/") or 0) if parsed.path and parsed.path != "/" else 0,
        "password": parsed.password,
    }


def get_redis_client():
    """
    Get a Redis client instance.

    Configuration priority:
    1. REDIS_URL environment variable (full connection string)
    2. REDIS_HOST + REDIS_PORT environment variables
    3. Falls back to in-memory cache if Redis is unavailable and ENVIRONMENT != production

    Returns a Redis client or InMemoryCache fallback.
    """
    environment = os.getenv("ENVIRONMENT", "development")
    redis_url = os.getenv("REDIS_URL")
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))

    try:
        import redis

        if redis_url:
            params = _parse_redis_url(redis_url)
            client = redis.Redis(
                host=params["host"],
                port=params["port"],
                db=params["db"],
                password=params["password"],
                decode_responses=False,
                socket_connect_timeout=5,
            )
        else:
            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=False,
                socket_connect_timeout=5,
            )

        # Test the connection
        client.ping()
        logger.info(f"Connected to Redis at {redis_url or f'{redis_host}:{redis_port}'}")
        return client

    except Exception as e:
        if environment == "production":
            logger.error(f"Failed to connect to Redis in production: {e}")
            raise

        logger.warning(
            f"Redis unavailable ({e}). Using in-memory cache fallback for development."
        )
        return InMemoryCache()


class RateLimitCache:
    """Redis-backed (or in-memory fallback) cache utility for rate limiting.

    Implements a sliding window counter pattern for rate limiting.
    """

    def __init__(self, client=None):
        self._client = client or get_redis_client()

    def is_rate_limited(
        self, key: str, max_requests: int, window_seconds: int
    ) -> bool:
        """
        Check if a key has exceeded the rate limit.

        Args:
            key: The rate limit key (e.g., "rate_limit:user:123:endpoint")
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            True if the key is rate limited, False otherwise.
        """
        current = self._client.incr(key)

        if current == 1:
            # First request in window, set expiry
            self._client.expire(key, window_seconds)

        return current > max_requests

    def get_remaining(
        self, key: str, max_requests: int
    ) -> int:
        """Get the number of remaining requests for a key."""
        value = self._client.get(key)
        if value is None:
            return max_requests
        current = int(value)
        return max(0, max_requests - current)

    def get_ttl(self, key: str) -> int:
        """Get time-to-live for a rate limit key in seconds."""
        return self._client.ttl(key)

    def reset(self, key: str) -> bool:
        """Reset a rate limit key."""
        return self._client.delete(key) > 0


# Module-level singleton (lazy initialization)
_redis_client = None
_rate_limit_cache = None


def get_redis():
    """Get the singleton Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = get_redis_client()
    return _redis_client


def get_rate_limit_cache() -> RateLimitCache:
    """Get the singleton rate limit cache."""
    global _rate_limit_cache
    if _rate_limit_cache is None:
        _rate_limit_cache = RateLimitCache(get_redis())
    return _rate_limit_cache
